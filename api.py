import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from tictactoe_models import User, Game, Score
from tictactoe_models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameForms, UserForm, UserForms
from lib import utils

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)

GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

USER_GAME_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(2),)

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),
    user_name=messages.StringField(2),)

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name="tic_tac_toe", version="v1")
class TicTacToeAPI(remote.Service):
    """ Tic Tac Toe API v1 """

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self,request):
        """Create a new User object. This method also 
            checks for unique user name. """

        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A user with the same name already exists!')
            return StringMessage('Error!')

        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message="User created successfully!")


    @endpoints.method(response_message=UserForms,
                      path = 'user/ranking',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self,request):
        """Sort the users according to their 'win percentage' """
        users = User.query(User.total_matches > 0).fetch()
        users = sorted(users, key=lambda x: x.win_percent, reverse=True) 
        # reverse = True is set to get the sort in DESCENDING order
        return UserForms(items=[user.to_form() for user in users])


    @endpoints.method(request_message=NEW_GAME_REQUEST,
                   response_message=GameForm,
                   path='game/new',
                   name='new_game',
                   http_method='POST')
    def new_game(self,request):
        """Create a New Game"""
        player_x = User.query(User.name == request.player_x).get()
        player_o = User.query(User.name == request.player_o).get()
        if not player_x and player_o:
            raise endpoints.NotFoundException(
                'One of the player\'s name doesn\'t exist')
        game = Game.create_game(player_x.key,player_o.key)
        return game.to_form()


    @endpoints.method(request_message=USER_GAME_REQUEST,
                   response_message=GameForms,
                   path='user/games',
                   name='get_user_games',
                   http_method='GET')
    def get_user_games(self,request):
        """Retrieves all the active games of User"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.BadRequestException('User not found!')
        games = Game.query(ndb.OR(Game.player_x == user.key,
                                  Game.player_o == user.key)).\
            filter(Game.is_game_over == False)
        return GameForms(items = [game.to_form() for game in games])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                   response_message=GameForm,
                   path='game/{urlsafe_game_key}',
                   name='get_game',
                   http_method='GET')
    def get_game(self,request):
        """Retrieve current Game state"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            endpoints.NotFoundException('Game not found!')
        else:
            return game.to_form()


    @endpoints.method(request_message=GET_GAME_REQUEST,
                   response_message=StringMessage,
                   path='game/{urlsafe_game_key}',
                   name='cancel_game',
                   http_method='DELETE')
    def cancel_game(self,request):
        """Check if game completed and then delete it"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if game and game.is_game_over:
            game.key.delete()
            return StringMessage('Game with key : {} deleted!'.
                format(request.urlsafe_game_key))
        elif game and game.is_game_over:
            raise endpoints.BadRequestException('Game has already ended!')
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                   response_message=GameForm,
                   path='game/{urlsafe_game_key}',
                   name='make_move',
                   http_method='PUT')
    def make_move(self,request):
        """Make a move on board.Return the new Game state"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.is_game_over:
            raise endpoints.NotFoundException('Game already over')

        # Check which Player's turn it is
        user = User.query(User.name == request.user_name).get()
        if user.key != game.next_move:
            raise endpoints.BadRequestException('It\'s not your turn!')
        
        # Just to assign proper(x,o) symbols to the respective players
        x = True if user.key == game.player_x else False
        move = request.move

        # Verify if move is between 0 and 8
        if move < 0 or move > 8:
            raise endpoints.BadRequestException('Invalid move. Must be between 0 and 8!')
        
        #Verify if cell on board is empty or not
        if game.board[move]!='':
            raise endpoints.BadRequestException('Invalid move. Cell already filled!')

        game.board[move] = 'X' if x else 'O'
        # Append a move to the history
        game.board_history.append(('X' if x else 'O', move))
        game.next_move = game.player_o if x else game.player_x
        
        winner = utils.check_winner(game.board)
        if not winner and utils.check_full(game.board):
            # Just delete the game
            game.key.delete()
            raise endpoints.NotFoundException('It\'s a tie! Game will be deleted!')
        if winner:
           game.end_game(user.key)
        else:
            # Send reminder email
            taskqueue.add(url='/tasks/send_move_email',
                          params={'user_key': game.next_move.urlsafe(),
                                  'game_key': game.key.urlsafe()})
        game.put()
        return game.to_form()


    @endpoints.method(request_message=GET_GAME_REQUEST,
                   response_message=StringMessage,
                   path='game/{urlsafe_game_key}/history',
                   name='get_game_history',
                   http_method='GET')
    def get_game_history(self,request):
        """Return a Game's moves history"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        else:
            return StringMessage(message = str(game.board_history))


    @endpoints.method(request_message=USER_REQUEST,
                   response_message=ScoreForms,
                   path='scores/user/{user_name}',
                   name='get_user_score',
                   http_method='GET')
    def get_user_scores(self,request):
        """Gets all User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(ndb.OR(Score.winner == user.key,
                                    Score.loser == user.key))
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        avg_attempts_remaining = memcache.get(MEMCACHE_MOVES_REMAINING)
        if not avg_attempts_remaining:
          avg_attempts_remaining="No moves remaining!"
        return StringMessage(message=avg_attempts_remaining)


    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.is_game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {: .2f}'.format(average))
        else:
          pass


api = endpoints.api_server([TicTacToeAPI])
