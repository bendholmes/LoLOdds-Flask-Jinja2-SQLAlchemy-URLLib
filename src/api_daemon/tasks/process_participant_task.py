# -*- coding: utf-8 -*-

from task import Task
from src.hextech_project_x import DB
from src.api.summoner.summoner_by_name import SUMMONER_BY_NAME
from src.api.stats.ranked_stats import RANKED_STATS
from src.domain.summoners import Summoners
from process_summoner_champion_task import ProcessSummonerChampionTask
from src.utils import getProfileIconUrl
from sqlalchemy.exc import OperationalError
from src.api.static.champion_by_id import CHAMPION_BY_ID
from src.utils import getChampionImageUrl

class ProcessParticipantTask(Task):
	def __init__(self, participantName, teamId, championId, game):
		self.participantName = participantName
		self.teamId = teamId
		self.championId = championId
		self.game = game

	"""
	Gets the summoner by the given participant name and processes its ranked stats if necessary.
	"""
	def run(self):
		currentSummoner = self.getCurrentSummoner()

		print "current summoner: %s" % currentSummoner

		# Grab the summoner data from their name
		success, summonerJSON = SUMMONER_BY_NAME.getSummoner(self.participantName)

		if not success:
			# TODO: Log this properly
			# TODO: What should we do about it?
			print "Failed to get summoner by name, got: %s" % summonerJSON
		else:
			print "got summoner %s" % summonerJSON

			# Get the current champion image URL
			# TODO: This should really be part of another system that maintains up to date links to static content,
			# but it'll do as a quick hack
			championImageUrl = getChampionImageUrl(CHAMPION_BY_ID.getChampionImageName(self.championId))

			# For brevity - get the dictionary for the summoner name (there's only ever one key which corresponds
			# to the summoner name)
			summonerJSON = summonerJSON[summonerJSON.keys()[0]]

			# Create the summoner object
			# Last stats modified and total wins / losses will be set by the champion with id 0 once we grab them shortly
			summonerId = int(summonerJSON["id"])

			summoner = Summoners(summonerId, summonerJSON["name"], getProfileIconUrl(summonerJSON["profileIconId"]),
				int(summonerJSON["revisionDate"]), 0, int(summonerJSON["summonerLevel"]), 0, 0, int(self.teamId),
				int(self.championId), championImageUrl)

			# Save or update the object
			self.saveOrUpdate(currentSummoner, summoner)

			# Process the ranked stats
			self.processRankedStats(summonerId, currentSummoner, summoner)

	"""
	Gets the ranked stats for this summoner and updates them if they have changed, otherwise it updates
	the summoner if that has changed.
	"""
	def processRankedStats(self, summonerId, currentSummoner, summoner):
		# Get summoner champion ranked stats
		success, rankedStatsJSON = RANKED_STATS.getStats(summonerId)

		if not success:
			# TODO: Log this properly
			# TODO: What should we do about it?
			print "Failed to get summoner ranked stats JSON, got: %s" % rankedStatsJSON
		else:
			# Check if we need to update the stats
			lastStatsModified = rankedStatsJSON["modifyDate"]
			if not currentSummoner or lastStatsModified > currentSummoner.lastStatsModified:
				self.updateRankedStats(summoner, lastStatsModified, rankedStatsJSON)

	"""
	Updates the summoners ranked stats if appropriate.
	"""
	def updateRankedStats(self, summoner, lastStatsModified, rankedStatsJSON):
		# Save the modified date
		summoner.lastStatsModified = lastStatsModified

		# Update all the stats
		for championJSON in rankedStatsJSON["champions"]:
			# Champion id 0 is an aggregate of all stats - we use this for the summoner object
			if championJSON["id"] == 0:
				summoner.totalSessionsWon = championJSON["stats"]["totalSessionsWon"]
				summoner.totalSessionsLost = championJSON["stats"]["totalSessionsLost"]
			else:
				summonerChampionTask = ProcessSummonerChampionTask(championJSON, summoner)
				summonerChampionTask.run()

		# Commit the changes
		self.update(summoner)

	def save(self, summoner):
		self.game.summoners.append(summoner)
		DB.session.add(summoner)
		# DB.session.commit()

	def update(self, summoner):
		# DB.session.merge(summoner)
		# DB.session.commit()
		pass

	def updateFromExistingSummoner(self, currentSummoner, summoner):
		summoner.totalSessionsWon = currentSummoner.totalSessionsWon
		summoner.totalSessionsLost = currentSummoner.totalSessionsLost
		self.game.summoners.append(summoner)
		self.update(summoner)

	"""
	Saves the summoner if it's new, or updates it if the data has changed.
	"""
	def saveOrUpdate(self, currentSummoner, summoner):
		if not currentSummoner:
			self.save(summoner)

		# Update the existing object if it has changed
		elif summoner.lastModified > currentSummoner.lastModified:
			self.updateFromExistingSummoner(currentSummoner, summoner)

	def getCurrentSummoner(self):
		# Get the existing summoner if it exists
		try:
			return Summoners.query.filter_by(name = self.participantName).first()
		except OperationalError, oe:
			print "Error loading current summoner: %s" % oe
		return None
