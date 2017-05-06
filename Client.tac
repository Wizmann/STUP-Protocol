import src.Client as Client
import src.Config as Config
from twisted.application import internet
from twisted.application import service

application = service.Application("Stup Client")
internet.TCPServer(Config.CLIENT_PORT, Client.factory)).setServiceParent(application)
