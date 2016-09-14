from time import sleep
import GSQuery

# Let's pick a server. We'll use TeamRectifier as they're usually populated.
gs = GSQuery.GSServer('31.186.250.42')

# Let's get the basic server details with the GameSpy query protocol.
# The query methods return dictionary types, so we can store them for later use
#   instead of having to ask the server every time we want to know something.
try: gs_bsd = gs.parse_query()
# Sometimes, our packets get lost, or the server is restarting. In that case,
#   we can just wait a few seconds, try again, and hope our query is returned.
except:
    sleep(5)
    gs_bsd = gs.parse_query()

# and find out the server's name
print "Server Name :", gs_bsd["hostname"]

# Now let's see what map they're on
print "Map Name    :", gs_bsd["mapname"]

# But what are they playing? (Assume the server name didn't make this obvious.)
# Let's see what game type is active.
print "Gametype    :", gs_bsd["gametype"]

# What game version do they use?
print "Game Version:", gs_bsd["gamever"]


#a little cleanup for what follows...
print "\n====\n"

# Why do all of these methods start with parse? This is because they take a
#   `query` argument, which is a raw query returned by UTServer.query().
# Specifying the `query` argument is optional, and the method will send the
#   necessary type of query needed if one is not provided.

################################################################################

# Unlike the query method used above, the player query method does not return a
#   dictionary of key-value pairs, but rather a list of UTPlayer objects.
#
# UTPlayer objects have six attributes:
# - Name, which is the colored name shown in-game, if colored names are used.
# - Score
# - Ping, in milliseconds. This ping value is the one shown in-game.
# - Team, which for team games is (red=0, blue=1). For DeathMatch, all players
#     have a team value of 0. Unlike UTQuery, spectators are not shown at all.
# - Player ID, which is simply the player's index in the GameSpy query response.
# - Stats ID, which the GameSpy protocol doesn't implement and is set to None.
#
# We can access these values through their values:
#   name, score, ping, team, pid, sid
# respectively.
#
# Let's start with getting the online player list.

gs_players = gs.parse_players()

# If we get an empty list, one of two things happened: either no players are
#   online, or our query was not returned. The server will return data if our
#   query was lost, but I haven't bothered to implement that check in my code
#   yet. 

# Now let's display their information. We really only care about name, score,
#   team, and ping. Since we are requesting information from a TeamArenaMaster
#   server, we are going to assume teams are present. For a DeathMatch server,
#   all players have a team value of 0, since there are no teams.

# First, we should check if players are online.
if len(gs_players) > 0:
    #If there are, let's display some information about them.
    print "Online Players:"
    for p in gs_players:
        # Skip anything with a ping of 0, as they're probably not real players.
        # Team scores appear as players with a ping of 0.
        if p.ping == 0: continue
        # Translate the team number to English. The rest are just numbers.
        team = ["red", "blue"][p.team]
        # Show their name, score, and ping. 
        print p.name + " is on " + team + " with a score of " + str(p.score) + \
              " and a ping of " + str(p.ping) + "ms."
# If we didn't find anyone online, we go here.
else:
    print "No online players!"
