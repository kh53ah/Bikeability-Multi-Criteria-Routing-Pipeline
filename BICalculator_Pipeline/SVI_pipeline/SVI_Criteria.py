class SVICriteria:
    """
    Contains all criteria functions for the Bikeability Index calculation.
    Each function receives the pixel area of a detected label, computes
    a raw criteria score, and multiplies it by its category weight before returning.
    To be implemented together later.
    """
    
    @staticmethod
    def Potholes_criteria():
        """Do Potholes NOT exist?"""
        return 1.0
    
    @staticmethod
    def Streetlights_criteria():
        """Do Street lights exist?"""
        return 1.0
    
    @staticmethod
    def BikeLanes_criteria():
        """Do Bike lanes exist?"""
        return 1.0
    
    @staticmethod
    def StreetAmenities_criteria(): # bike racks and benches
        """Do Street Amenities exist?"""
        return 1.0
    
    @staticmethod
    def UtilityPole_criteria(): #electricity poles
        """Do Utility Poles NOT exist?"""
        return 1.0
    
    @staticmethod
    def SideWalk_criteria():
        """Does a Side Walk exist?"""
        return 1.0
    
    @staticmethod
    def TrafficLights_criteria():
        """Does a Traffic light NOT exist?"""
        return 1.0
    
    @staticmethod
    def CatchBasin_criteria():
        """Does a Catch Basin NOT exist?"""
        return 1.0

    @staticmethod
    def Scenery_criteria():
        """Scenery: greenery, buildings or water"""
        return 1.0

    @staticmethod
    def TramRails_criteria():
        """Do Traum Rails NOT exist?"""
        return 1.0
    
    @staticmethod
    def CrossWalk_criteria():
        """Does a Cross Walk NOT exist?"""
        return 1.0
    
    @staticmethod
    def CurbCuts_criteria():
        """Does a Curb Cut NOT exist?"""
        return 1.0
