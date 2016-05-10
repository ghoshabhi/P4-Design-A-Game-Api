import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class User(ndb.Model):
    """Object for User's Profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    wins = ndb.IntegerProperty(default=0)
    total_matches = ndb.IntegerProperty(default=0)

    @property
    def win_percent(self):
        if self.total_matches > 0:
            return ((float(self.wins)/float(self.total_matches))*100)
        else:
            return 0

    def to_form(self):
        return UserForm(name = self.name,
                        email = self.email,
                        wins = self.wins,
                        total_matches = self.total_matches,
                        win_percent = self.win_percent)

    def add_win(self):
        """Add +3 to the win count"""
        self.wins += 1
        self.total_matches += 1
        self.put()

    def add_loss(self):
        """Add +1 to total_matches count"""
        self.total_matches += 1
        self.put()


class Score(ndb.Model):
    """Model class for Score object"""
    date = ndb.DateProperty(required=True)
    winner = ndb.KeyProperty(required=True)
    loser = ndb.KeyProperty(required=True)

    def to_form(self):
        return ScoreForm(date = str(self.date),
                         winner = self.winner.get().name,
                         loser = self.loser.get().name)


class Game(ndb.Model):
    """Object for Game Class"""
    board = ndb.PickleProperty(required=True)
    next_move = ndb.KeyProperty(required=True)
    player_x = ndb.KeyProperty(required=True,kind=User)
    player_o = ndb.KeyProperty(required=True,kind=User)
    is_game_over = ndb.BooleanProperty(required=True,default=False)
    winner = ndb.KeyProperty()
    board_history = ndb.PickleProperty(required=True)


    @classmethod
    def create_game(cls,player_x,player_o):
        """Creates a new Game and returns it"""
        game = Game(player_o=player_o,
                    player_x=player_x,
                    next_move=player_x)
        """Initialise the board"""
        game.board = ['' for _ in range(9)]
        game.board_history = []
        game.put()
        return game

    def to_form(self):
        """Returns a GameForm representaion of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        board = str(self.board),
                        player_x = self.player_x.get().name,
                        player_o = self.player_x.get().name,
                        next_move = self.next_move.get().name,
                        is_game_over = self.is_game_over,
                        winner = ""
                        )
        if self.winner:
            form.winner = self.winner.get().name
        return form 

    def end_game(self,winner):
        """End the Game and Update the 'Score'"""
        if winner:
            self.winner = winner
            self.is_game_over = True
            self.put()
            loser = self.player_o if winner == self.player_x else self.player_x
            # Update the score board
            score = Score(date=date.today(),winner=winner,loser=loser)
            score.put()

            # Update the User models
            winner.get().add_win()
            loser.get().add_loss()


class GameForm(messages.Message):
    """GameForm to outbound Game information"""
    urlsafe_key = messages.StringField(1,required=True)
    board = messages.StringField(2,required=True)
    player_x = messages.StringField(3,required=True)
    player_o = messages.StringField(4,required=True)
    next_move = messages.StringField(5,required=True)
    is_game_over = messages.BooleanField(6,required=True)
    winner = messages.StringField(7,required=True)


class GameForms(messages.Message):
    """Resource Container for multiple Game Forms"""
    items = messages.MessageField(GameForm,1,repeated=True)


class NewGameForm(messages.Message):
    """Resource container to create New Game"""
    player_x = messages.StringField(1,required=True)
    player_o = messages.StringField(2,required=True)


class MakeMoveForm(messages.Message):
    """Resource container to Make a Move"""
    name = messages.StringField(1,required=True)
    move = messages.IntegerField(2,required=True)


class ScoreForm(messages.Message):
    """Resource container to outbound Score information"""
    date = messages.StringField(1,required=True)
    winner = messages.StringField(2,required=True)
    loser = messages.StringField(3,required=True)


class ScoreForms(messages.Message):
    """Resource container for multiple forms"""
    items = messages.MessageField(ScoreForm,1,repeated=True)


class StringMessage(messages.Message):
    """String Message to outbound send a String Message"""
    message = messages.StringField(1,required=True)


class UserForm(messages.Message):
    """Resource container to outbound User information"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    wins = messages.IntegerField(3, required=True)
    total_matches = messages.IntegerField(4, required=True)
    win_percent = messages.FloatField(5, required=True)


class UserForms(messages.Message):
    """Resource container for multiple User Forms"""
    items = messages.MessageField(UserForm,1,repeated=True)
