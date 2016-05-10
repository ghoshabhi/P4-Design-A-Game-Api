import logging
from google.appengine.ext import ndb
import endpoints

def get_by_urlsafe(urlsafe, model):
    """Returns an entity based on the Key provided"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity


def check_winner(board):
    """Check the board. If there is a winner, return the symbol of the winner"""
    # For rows the starting position is : 0,3,6. The positions shift in the form : i|i+1|i+2 and the 
    # the values of i are incremented by 3 after each iteration to move to the next row directly!
    for i in range(3):
        if board[3*i]:
            if board[3*i] == board[3*i + 1] and board[3*i] == board[3*i + 2]:
                return board[3*i]
    # For columns the starting position is 0,1,2! The positions shift in the form : i,i+3,i+6. Here the value
    # of i is not multiplied by 3 as the shift happens directly by adding to the index.
    for i in range(3):
        if board[i]:
            if board[i] == board[i + 3] and board[i] == board[i + 6]:
                return board[i]
    # Possible positions to win in diagnols are only 2 : 0,4,8 or 2,4,6. Both 
    # the possibilities are checked one by one.
    if board[0]:
        if board[0] == board[4] and board[0] == board[8]:
            return board[0]
    if board[2]:
        if board[2] == board[4] and board[2] == board[6]:
            return board[2]

def check_full(board):
    """Return true if the board is full"""
    for each_cell in board:
        if not each_cell:
            return False
    return True