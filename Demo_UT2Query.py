from time import sleep
import UTQuery

# Let's pick a server. We'll use TeamRectifier as they're usually populated.
us = UTQuery.UTServer('31.186.250.42')

# Let's get the basic server details with the Unreal2 query protocol.
# The query methods return dictionary types, so we can store them for later use
#   instead of having to ask the server every time we want to know something.
try: us_bsd = us.parse_query()
# Sometimes, our packets get lost, or the server is restarting. In that case,
#   we can just wait a few seconds, try again, and hope our query is returned.
except:
    sleep(5)
    us_bsd = us.parse_query()

# and find out the server's name
print "Server Name :", us_bsd["Server Name"]

# Now let's see what map they're on
print "Map Name    :", us_bsd["Map Name"]

# But what are they playing? (Assume the server name didn't make this obvious.)
# Let's see what game type is active.
print "Gametype    :", us_bsd["Game Type"]

################################################################################

# But who runs this server, and what version is the server? This info isn't in
#   the basic server query, so we need to use the Extended Server Data query
#   type. Unlike the basic server info, extended server info does not have
#   spaces in the key names. This is because the server provides the key names
#   in extended queries, whereas basic queries do not.
#
# Extended queries are only available in UTQuery; GSQuery does not have an
#   equivalent method, as the GameSpy protocol does not implement this. 
try:
    us_esd = us.parse_exquery()
except:
    sleep(5)
    us_esd = us.parse_exquery()

# Let's find the server version (GSQuery can also do this). 
print "Game Version:", us_esd["ServerVersion"]

# Let's now find the admin of the server...
print "Admin Name  :", us_esd["AdminName"]
# Now we can find out how to contact that admin
print "Admin Email :", us_esd["AdminEmail"]


#a little cleanup for what follows...
print "\n====\n"

# Why do all of these methods start with parse? This is because they take a
#   `query` argument, which is a raw query returned by UTServer.query().
# Specifying the `query` argument is optional, and the method will send the
#   necessary type of query needed if one is not provided.

################################################################################

# Unlike the query functions used above, the player query method does not return
#   a dictionary of key-value pairs, but rather a list of UTPlayer objects.
#
# UTPlayer objects have six attributes:
# - Name, which is the colored name shown in-game, if colored names are used.
# - Score
# - Ping, in milliseconds. This ping value is the one shown in-game.
# - Team, which for team games is (spectator=0, red=1, blue=2). For DeathMatch,
#     all players and spectators have a team value of 0.
# - Player ID, which isn't used.
# - Stats ID, which usually isn't used.
#
# We can access these values through their values:
#   name, score, ping, team, pid, sid
# respectively.
#
# Let's start with getting the online player list.

us_players = us.parse_players()

# If we get an empty list, one of two things happened: either no players are
#   online, or our query was not returned. There's no way for the code to know,
#   since querying the server with no players online will not return any data.

# Now let's display their information. We really only care about name, score,
#   team, and ping. Since we are requesting information from a TeamArenaMaster
#   server, we are going to assume teams are present, even though the server
#   identifies itself as xDeathMatch. For a proper xDeathMatch server, there is
#   no way to separate spectators from players, as all have a team value of 0.

# First, we should check if players are online.
if len(us_players) > 0:
    #If there are, let's display some information about them.
    print "Online Players:"
    for p in us_players:
        # Skip anything with a ping of 0, as they're probably not real players.
        # Team scores appear as players with a ping of 0.
        if p.ping == 0: continue
        # Translate the team number to English. The rest are just numbers.
        team = ["a spectator", "on red", "on blue"][p.team]
        # Show their name, and prepare to show the rest of the info
        print p.name + " is " + team + " with",
        # Only show the score if they're not spectating.
        if p.team:
            print "a score of " + str(p.score) + " and",
        print "a ping of " + str(p.ping) + "ms."
# If we didn't find anyone online, we go here.
else:
    print "No online players!"
