from fractions import gcd
from collections import defaultdict
from src.utils import getTeamName

class GameOddsService(object):
	DEFAULT_ODDS = "1 : 1"
	DEFAULT_PERCENTAGE = 50

	"""
	Cumulates the total (and current champion) wins and losses for each team for each game, calculates
	the odds based on these totals and records all the data along with team summoner information in
	a dictionary for passing to the UI to display.

	NOTE: This currently calculates odds based on total values per team, i.e:

	all team summoners wins / (all team summoners wins + all team summoners losses)

	It may be more meaningful to do this on a player by player basis using their individual win
	rates to get a team win rate average, i.e:

	(player1 wins / (player1 wins + player1 losses) + ... + playerN wins / (playerN wins + playerN losses)) * team size

	Then the odds would be calculated by comparing both team's win rate averages. This would give more weight
	towards individual players, making weak and strong players have a greater skew of the odds.
	"""
	def getGamesWithOdds(self):
		# Grab all the games, latest first
		# TODO: Add a date/time field to the Games table and order on that
		games = Games.query.order_by(Games.gameId.desc()).all()

		gameList = []
		for game in games:
			teams = defaultdict(list)
			teamWinsAndLosses = defaultdict(lambda: defaultdict(int))
			for gameSummoner in game.summoners:
				# Accumulate the team total wins and losses
				# TODO: Reduce this repetition?
				teamWinsAndLosses[getTeamName(gameSummoner.teamId)]["wins"] += gameSummoner.totalSessionsWon
				teamWinsAndLosses[getTeamName(gameSummoner.teamId)]["losses"] += gameSummoner.totalSessionsLost
				teamWinsAndLosses[getTeamName(gameSummoner.teamId)]["championWins"] += gameSummoner.totalChampionSessionsWon
				teamWinsAndLosses[getTeamName(gameSummoner.teamId)]["championLosses"] += gameSummoner.totalChampionSessionsLost

				# Add the summoner to the teams list
				teams[getTeamName(gameSummoner.teamId)].append({
					"name": gameSummoner.summoner.name,
					"championImageUrl": gameSummoner.championImageUrl,
					"winRate": self._getPercentage(gameSummoner.totalSessionsWon, gameSummoner.totalSessionsLost),
					"championWinRate": self._getPercentage(gameSummoner.totalChampionSessionsWon, gameSummoner.totalChampionSessionsLost),
					"level": gameSummoner.summoner.level
				})

			# If there are no stats for either team then report 1:1
			if len(teamWinsAndLosses) < 2:
				odds = GameOddsService.DEFAULT_ODDS
				championOdds = GameOddsService.DEFAULT_ODDS
			else:
				# TODO: Reduce this repetition?
				# TODO: Our UI displays teams as BLUE (200) vs PURPLE (100) so do the ratio in this order - i'm really
				# not happy about how brittle this is, and need to do it better in the future
				odds = self._calculateGameOdds(teamWinsAndLosses["BLUE"]["wins"],
					teamWinsAndLosses["BLUE"]["losses"],
					teamWinsAndLosses["PURPLE"]["wins"],
					teamWinsAndLosses["PURPLE"]["losses"])
				championOdds = self._calculateGameOdds(teamWinsAndLosses["BLUE"]["championWins"],
					teamWinsAndLosses["BLUE"]["championLosses"],
					teamWinsAndLosses["PURPLE"]["championWins"],
					teamWinsAndLosses["PURPLE"]["championLosses"])

			# Add the game to the list
			gameList.append({ "teams": teams, "odds": odds, "championOdds": championOdds, "mode": game.gameMode,
				"queue": game.gameQueueId })

		# Commit even though nothing has changed to tell SQLAlchemy the transaction has ended - without
		# this the Games query would be "cached" each time without a server reboot
		DB.session.commit()

		return gameList

	"""
	Gets the win percentage for each team, finds their relative chances of winning and
	then finds the greatest common divisor to convert to the odds ratio.
	"""
	def _calculateGameOdds(self, blueTotalWins, blueTotalLosses, purpleTotalWins, purpleTotalLosses):
		blueWinPercentage = self._getPercentage(blueTotalWins, blueTotalLosses)
		purpleWinPercentage = self._getPercentage(purpleTotalWins, purpleTotalLosses)

		blueChance = self._getPercentage(blueWinPercentage, purpleWinPercentage)
		purpleChance = self._getPercentage(purpleWinPercentage, blueWinPercentage)

		greatestCommonDivisor = gcd(blueChance, purpleChance)
		if greatestCommonDivisor == 0:
			greatestCommonDivisor = 1

		return "%i : %i" % (blueChance / greatestCommonDivisor, purpleChance / greatestCommonDivisor)

	def _getPercentage(self, i1, i2):
		# In this context, if both values are 0 that means there's no data on wins or losses, so lets call
		# the chance of a win or loss 50/50
		if i1 == 0 and i2 == 0:
			return GameOddsService.DEFAULT_PERCENTAGE
		return round((float(i1) / (i1 + i2)) * 100)

GAME_ODDS_SERVICE = GameOddsService()

from src.hextech_project_x import DB
from src.domain.games import Games
from src.domain.game_summoners import GameSummoners
from src.domain.summoners import Summoners
from src.domain.summoner_champion_stats import SummonerChampionStats