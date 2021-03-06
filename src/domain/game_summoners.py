from src.hextech_project_x import DB

"""
Represents an instance of a summoner playing a specific champion in a specific team in a specific game.

Records the total ranked and champion stats the summoner had at the time when playing the game.

There will always be one entry in this table per summoner per game so that we can recall the details of
each summoner in the game at any point, without future games affecting the data.
"""
class GameSummoners(DB.Model):
    gameId = DB.Column(DB.BigInteger, DB.ForeignKey('games.gameId'), primary_key = True, autoincrement = False)
    summonerId = DB.Column(DB.BigInteger, DB.ForeignKey('summoners.summonerId'), primary_key = True, autoincrement = False)
    totalSessionsWon = DB.Column(DB.Integer)
    totalSessionsLost = DB.Column(DB.Integer)
    totalChampionSessionsWon  = DB.Column(DB.Integer)
    totalChampionSessionsLost  = DB.Column(DB.Integer)
    teamId = DB.Column(DB.Integer)
    championId = DB.Column(DB.Integer)
    championImageUrl = DB.Column(DB.String(255)) # TODO: This should be stored in its own image table to prevent redundancy

    summoner = DB.relationship('Summoners', backref = DB.backref('GameSummoners', lazy='joined'), lazy='joined')

    def __init__(self, gameId, summonerId, totalSessionsWon, totalSessionsLost, totalChampionSessionsWon,
            totalChampionSessionsLost, teamId, championId, championImageUrl):
        self.gameId = gameId
        self.summonerId = summonerId
        self.totalSessionsWon = totalSessionsWon
        self.totalSessionsLost = totalSessionsLost
        self.totalChampionSessionsWon = totalChampionSessionsWon
        self.totalChampionSessionsLost = totalChampionSessionsLost
        self.teamId = teamId
        self.championId = championId
        self.championImageUrl = championImageUrl

    def __repr__(self):
        return '<GameSummoners %i>' % self.summonerId
