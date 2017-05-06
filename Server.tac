import src.Server as Server
import src.Config as Config
from twisted.application import internet
from twisted.application import service

application = service.Application("Stup Server")
internet.UDPServer(Config.SERVER_PORT, Server.StupServerFactoryProtocol()).setServiceParent(application)
