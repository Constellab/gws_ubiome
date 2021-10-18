# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi.requests import Request

class API:
    """
    API class to represents custom REST API entry points of your brick
    """
    
    @staticmethod
    def my_entry_point(request: Request):
        """
        Custom entry point function.
        
        Suppose that url of the lab is `https://lab.gencovery.com` and that this brick is named `gws_ubiome`.
        Then, the API route `https://lab.gencovery.com/brick-api/gws_ubiome/my_entry_point` is accessible using GET, POST requests
        and will pass through this function
        
        :param request: The FastAPI request object
        :type request: `fastapi.requests.Request`
        :return: The JSON response
        :rtype: dict
        """
        
        # do the job here ...
        
        api_response = {}
        return api_response
    