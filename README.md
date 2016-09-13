# UTQuery
UT2004 Server Query Protocol, in Python 2.7

## UTQuery

UTQuery allows you to query a UT2004 (maybe even UT2003) server using the UT2 Server Query protocol, usually on port 7778. It sends a packet to the server requesting information, and parses and returns received data. There are three poorly named methods you can use on a UTServer object to request data:
- parse_query(): parses a Basic Server Info packet. 
- parse_exquery(): parses an Extended Server Info packet.
- parse_players(): returns a list of players on server, in UTPlayer objects.

UTPlayer objects are a simple storage class implementing some UT2004-specific features, like removing 3SPN/UTComp color codes from names. The constructor for the class is pretty straightforward. 

## GSQuery
UTQuery using GameSpy query. Spectators and team scores are not visible, but correct ping values are shown and data is updated instantly. It is nearly a drop-in replacement for UTQuery, aside for some differences. Team indices are different (in non-team modes, 0 is the only team; in team modes, 0 is red team and 1 is blue team), the player ID is the index of the player in the GameSpy packet, and the stats ID is not available (set to None). It does not allow packets to arrive out of sequence yet. 

## RemoteScoreboard
This is an example program, written for both UTQuery and GSQuery, that displays the scores and pings of all connected players. It isn't the most efficient, but it is a good working proof of concept. 
Command line syntax: python remotescoreboard.py server-ip [port [override-xDeathMatch]]
override-xDeathMatch forces RemoteScoreboard to assume there is a team match. This is because 3SPN v3.223hl identifies in UTQuery (but not GSQuery) as xDeathMatch instead of TeamArenaMaster/Freon, allowing the server to appear in the UT2004 Master Server Browser without the user having to install 3SPN on their client, but this has the side-effect of confusing UTQuery. 

## A Note
I have tried to make this cross-platform, but I have only tested this on Windows with an 80-character-wide command prompt. UTQuery/GSQuery should work without problems cross-platform (except for systems with different endianness because of the way I use struct.unpack()), but I make no guarantees that RemoteScoreboard will display properly on other platforms. 
