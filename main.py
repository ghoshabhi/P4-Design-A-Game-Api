import logging
import webapp2
from google.appengine.api import mail, app_identity
from google.appengine.ext import ndb
from api import TicTacToeAPI
from lib import utils
from tictactoe_models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email who has
        games in progress. Email body includes the count and 
        URL Safe Keys of all the active games.
        Called every 4 hours using a cron job"""
        
        users = User.query(User.email != None)
        for user in users:
            games = Game.query(ndb.OR(Game.player_x == user.key,
                                     Game.player_o == user.key)).\
                filter(Game.is_game_over == False)
            if games.count() > 0:
                subject = 'This is a reminder!'
                body = 'Hello {}, you have {} games in progress. Their' \
                       ' keys are: {}'.\
                    format(user.name,
                           games.count(),
                           ', '.join(game.key.urlsafe() for game in games))
                logging.debug(body)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.
                               format(app_identity.get_application_id()),
                               user.email,
                               subject,
                               body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game average moves remaining announcement in memcache."""
        TicTacToeAPI._cache_average_attempts()
        self.response.set_status(204)


class SendMoveEmail(webapp2.RequestHandler):
    def post(self):
        """Send an email to a User that it is their turn"""
        game = utils.get_by_urlsafe(self.request.get('game_key'), Game)
        
        user_key = game.next_move
        user = user_key.get()
        
        subject = 'It\'s your turn in Tic Tac Toe!'
        body = '{}, It\'s your turn to play Tic Tac Toe. The game key is: {}'.\
           format(user.name, game.key.urlsafe())
        logging.debug(body)
        mail.send_mail('noreply@{}.appspotmail.com'.
                               format(app_identity.get_application_id()),
                               user.email,
                               subject,
                               body)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
    ('/tasks/send_move_email', SendMoveEmail),
], debug=True)
