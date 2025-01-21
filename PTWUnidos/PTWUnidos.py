import pyvisa
import time

class PTWUnidos:

    """Class for remote comunication with the PTW UNIDOS electrometer
    
    Attributes
    ----------
    serial : pyvisa resource
        Open port for electrometer comunication.
    serNo : str
        Serial number of the electrometer.
    version : str
        Version of the firmware.

    Methods
    -------
    getFlags()
        Retrieve information of the electrometer.
    getPosition()
        Get the current position of the cursor in the electrometer.
    getStatus()
        Get the current status of the electrometer.
    getRange()
        Get the current range of the electrometer.
    getVoltage(goToSetup = True)
        Get the current voltage of the electrometer.
    getUnit()
        Get the unit in with the measurement is made.
    getIntegrationTime(goToSetup = True)
        Get the current integration time set in the electrometer.
    getCorrections()
        Get correction of applied by the electrometer
    getReading()
        Get a list with the data on the screen of the electrometer.

    setElectricalUnits()
        Set the electrical units in the electrometer.
    setRange(range)
        Set the range of the electrometer.
    setVoltage(voltage)
        Set voltage on the electrometer.
    setIntegrationTime(integrationTime)
        Set the integration time.

    integrate()
        Perform an integration.
    doNull()
        Perform a null in the electrometer.
    goToSetupPosition()
        Go to the charge mode and set the cursor in the setup menu.
    close()
        Close the communication with the electrometer.

    """

    def __init__(self, serialPort: str) -> None:

        """
        Parameters
        ----------
        serialPort : str
            String with the direction of the port where the instrument is
            conected.

        """

        rm          = pyvisa.ResourceManager()
        self.serial = rm.open_resource(serialPort)

        ## configuration
        self.serial.baud_rate         = 9600
        self.serial.parity            = False
        self.serial.timeout           = 3000
        self.serial.data_bits         = 8
        self.serial.read_termination  = '\r\n'
        self.serial.write_termination = '\r\n'

        ## List of voltages admitted by the electrometer
        self.__listOfVoltages = [0, 50, 100, 150, 200, 250, 300, 350, 400]


        if self._sendCommand("PTW", False).split(" ")[0] == "UNIDOS":
        
            self.version = self._sendCommand("PTW", False).split(" ")[1]
            self.serNo   = self._sendCommand("SER", False)
        
            print(f"PTW {self.version} electrometer. Serial number: {self.serNo}")

        else: print("This is not an UNIDOS electrometer")

        # This code only works with Electric units. Then, the first thing is set 
        # the electrometer in electrical units.
        self.setElectricalUnits()

    @property
    def listOfVoltages(self) -> list:
        """Getter for the list of allowed voltages.

        Returns
        -------
        list
            List of ints with the values of the avaliable voltages to set.
        """

        return self.__listOfVoltages
    
    def getFlags(self) -> str:
        """Retrieve information of the electrometer."""
        response = int(self._sendCommand("?F", False))
        return f'{response:08b}'
    
    def setElectricalUnits(self) -> None:
        """Set the electrical units in the electrometer rather than the
        radiological ones."""
        
        if self.getFlags()[-3] == "1":

            # Go to setup position
            self.goToSetupPosition()
            # Enter the chamber menu
            self._sendCommand("E")
            # Go one step down
            self._sendCommand("D")
            # Change the units
            self._sendCommand("E")
            self._sendCommand("U")
            self._sendCommand("E")
            # Ask for the units
            if self.getFlags()[-3] == "1":
                print("Electrical units not set correctly")

            self.goToSetupPosition()
    
    def getPosition(self) -> str:
        """Get the current position of the cursor in the electrometer.
        
        Returns
        -------
        str
            Current position in terms of numbers (see documentation).        
        """
        return self._sendCommand("?W", False)
    
    def getStatus(self) -> str:
        """Get the current status of the electrometer.
        
        Returns
        -------
        str
            Current status of the electrometer.
        """

        return self._sendCommand("?S", False)
    
    def doNull(self) -> None:
        """Perform a null in the electrometer. This operation takes 75 s."""
        
        self._sendCommand("N", False)
        time.sleep(75)

        while self.getStatus() == "NUL":
            time.sleep(5)

    def goToSetupPosition(self) -> None:
        """Go to the charge mode and set the cursor in the setup menu."""

        r = self.getPosition()

        while r != "00":

            if len(r) > 2   : self._sendCommand("C")
            elif r[0] != "0": self._sendCommand("M0")
            elif r[1] != "0": self._sendCommand("U")

            r = self.getPosition()

    def setRange(self, range: str) -> None:
        """Set the range of the electrometer.
        
        Parameters
        ----------
        range : str
            Range to set. Notice that in charge mode only two ranges are
            allowed, namely low and high.

        Raises
        ------
        AssertionError
            If range is not Low, Medium or High.            
        """

        # Assert range is in the list.
        assert range in ["Low", "Medium", "High"], "Range not recognised"

        # Get the correct number to set the range.
        if range == "Low" or range == "low":       x = 0
        if range == "Medium" or range == "medium": x = 1
        if range == "High" or range == "high":     x = 2

        # Send the command to set the range.
        self._sendCommand(f"R{x}")


    def getRange(self) -> list[str, str]:
        """Get the current range of the electrometer.
        
        Returns
        -------
        [str, str]
            The first element correcpond to the range and the second element to 
            the maximum value of the range.

        """
        
        response      = self._sendCommand("?R", False)
        splitResponse = response.split(" ")

        range = ""
        for string in splitResponse:
            if len(string) > 1: 
                range = string 
                break

        return range, f"{splitResponse[2]} {splitResponse[3]}C"
    
    def getVoltage(self, goToSetup: bool = True) -> int:
        """Get the current voltage of the electrometer.
        
        Parameters
        ----------
        goToSetup : bool [optional, default = True]
            Go to the setup positions once the voltage is set.

        Returns
        -------
        int
            Value of the current voltage set in the electrometer.
        """
        
        # Go to setup position
        self.goToSetupPosition()
        # Go to the chamber menu
        self._sendCommand("D")
        # Enter the chamber menu
        self._sendCommand("E")
        # In the chamber menu we have to go down one time
        self._sendCommand("D")
        # Press enter to go insided the value
        self._sendCommand("E")
        # Get the actual value
        aValue = self._sendCommand("V", False)

        # Return to reference position (if asked).
        if goToSetup: self.goToSetupPosition()

        return int(aValue.split()[0])

    def setVoltage(self, voltage: int) -> None:
        """Set voltage on the electrometer

        Parameters
        ----------
        voltage: int
            Voltage to set in the electrometer.

        Raises
        ------
        AsertionError
            If voltage is not in the list of allowed voltages
        """

        assert voltage in self.listOfVoltages, f"{voltage} V is not a valid value of voltage"

        # Get the current value of the voltage and do not go to 
        # setup menu
        aVoltage = self.getVoltage(False)

        currentVoltageIndex = self.listOfVoltages.index(aVoltage)
        newVoltageIndex = self.listOfVoltages.index(voltage)

        move = newVoltageIndex - currentVoltageIndex
        if move > 0: [self._sendCommand("U") for i in range(move)]
        if move < 0: [self._sendCommand("D") for i in range(-move)]

        # Check that the new voltage is correctly set
        if voltage != int(self._sendCommand("V", False).split()[0]):
            print("Error setting the requested voltage, operation aborted.")
        else:
            # Press ENT
            response = self._sendCommand("E", False)
            # If the response is not Enter, we have probably to press STA key
            if response != "E": self._sendCommand("G", False)

        self.goToSetupPosition()

    def getUnit(self) -> str:
        """Get the unit in with the measurement is made.

        Return
        -------
        str
            Unit.
        """

        return self._sendCommand("?U", False)

    def getIntegrationTime(self, goToSetup: bool = True) -> int:
        """Get the current integration time set in the electrometer

        Parameters
        ----------
        goToSetup : bool [optional, default = True]
            If True, go to setup position.

        Return
        ------
        int
            Current set integration time.
        """

        # Go to setup position
        self.goToSetupPosition()
        # Go to the setup menu
        self._sendCommand("E")
        # Go to the setup menu
        self._sendCommand("E")
        # Get the actual value
        aValue = self._sendCommand("V", False)
        # Return to reference position
        if goToSetup: self.goToSetupPosition()

        return int(aValue)

    def setIntegrationTime(self, integrationTime: int):
        """Set the integration time.

        Parameters
        ----------
        integrationTime: int
            integration time to be set.

        Raises
        ------
        AssertionError
            If integration time is not < 9999 or is not an integer
            
        """

        assert type(integrationTime) is int and integrationTime >= 6 and integrationTime <= 9999, \
            f"{integrationTime} s is not a valid value of integration time"

        # Go to setup position
        self.goToSetupPosition()
        # Go to the setup menu
        self._sendCommand("E")
        # Go to the setup menu
        self._sendCommand("E")
        # Send the integration time
        self._sendCommand(f"{integrationTime}".zfill(4))

        self._sendCommand("E")
        # Check that the new integration time is correctly set
        if integrationTime != int(self._sendCommand("V", False)):
            print("Error setting the integration time, operation aborted.")

    def integrate(self) -> float:
        """Perform an integration.

        Returns
        -------
            Value of the charge.
        """

        # Check where the electrometer is
        if self.getPosition()[0] != "00":
            self.goToSetupPosition()

        # Check the integration time
        integrationTime = self.getIntegrationTime()

        # Integrate in the electrometer
        start = time.time()
        self._sendCommand("I")

        time.sleep(integrationTime + 1)

        while self.getStatus() == "INT": time.sleep(1)

        self.serial.write('V')
        results      = self.serial.read_raw().decode("latin1").split(" ")
        validResults = [value for value in results if len(value) > 1]
        iTime        = validResults[0][:-1]

        if int(iTime) != integrationTime:
            print("Integration time missmatch")

        charge = float(validResults[1])
        return charge

    def _sendCommand(self, command: str, crossCheck: bool = True) -> str:
        """Send a command to the electrometer

        Parameters
        ----------
        command : str
            Command to be send
        crossCheck : bool [optional, default = True]
            If True checks if the electrometer responds correctly.

        Returns
        -------
        str
            String with the electrometer response.
        """

        response = self.serial.query(command)
        if response != command and crossCheck: 
            print(f"Error sending command: {command}")

        return response

    def getCorrections(self) -> str:
        """Get correction of applied by the electrometer.

        Returns
        -------
        str
            String with the corrections.
        """

        return self._sendCommand("?C", False)
    
    def getReading(self) -> list[str]:
        """Get a list with the data on the screen of the electrometer.
        
        Returns
        -------
        list[str]
            List with the data in the screen of the electrometer.
        """

        return self._sendCommand("V", False).split(" ")

    def close(self) -> None:
        """Close the communication with the electrometer."""

        self._sendCommand("T1")
        self.serial.close()