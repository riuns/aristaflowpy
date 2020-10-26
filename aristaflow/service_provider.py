from .rest_helper import RestPackageRegistry, RestPackage, RestPackageInstance
from af_org_model_manager.models.client_session_details import ClientSessionDetails
from typing import Type, TypeVar

T = TypeVar('T')

class ServiceProvider(object):
    """ Per user session service provider caching service stubs and providing authentication data to them.
    """
    __rest_package_registry: RestPackageRegistry = None
    # package to package instance map
    __rest_packages: [RestPackage, RestPackageInstance] = None
    # cached service stubs
    __services: [type, object] = None
    # authentication
    __csd: ClientSessionDetails = None

    def __init__(self, rest_package_registry: RestPackageRegistry):
        self.__rest_package_registry = rest_package_registry
        self.__rest_packages = {}
        self.__services = {}

    def get_service(self, service_type: Type[T]) -> T:
        """
        Returns a service instance for the given service type, e.g.
        get_service(InstanceControlApi)
        @param service_type The class of the requested service.
        """
        # return a cached instance
        if service_type in self.__services:
            return self.__services[service_type]

        # find the package description and package instance
        pkg = self.__rest_package_registry.get_rest_package(service_type)
        pkg_instance: RestPackageInstance = None
        if pkg in self.__rest_packages:
            pkg_instance = self.__rest_packages[pkg]
        else:
            pkg_instance = RestPackageInstance(pkg)

        # get the ApiClient object of the package
        api_client = pkg_instance.api_client
        # authentication data
        if self.__csd:
            self.__use_authentication(api_client)
        # instantiate the service
        service = service_type(api_client)
        # cache it
        self.__services[service_type] = service
        return service

    def __use_authentication(self, api_client: object):
        """Uses the client session details to set the default header
        """
        api_client.set_default_header("x-AF-Security-Token", self.__csd.token)

    def authenticated(self, csd:ClientSessionDetails):
        """ set the authentication for all ApiClient objects
        """
        if self.__csd != None:
            raise Exception("Already authenticated")

        self.__csd = csd
        for _, inst in self.__rest_packages:
            self.__use_authentication(inst.api_client)