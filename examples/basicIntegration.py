from PTWUnidos import PTWUnidos

electrometer = PTWUnidos("ASRL/dev/ttyUSB0::INSTR")

# Set voltage and integration time
electrometer.setVoltage(300)
electrometer.setRange("Low")
electrometer.setIntegrationTime(30)

# Integrate the charge
charge = electrometer.integrate()
print(f"{charge:.3E} C")

# Set Voltage to zero and close conection with the electrometer
electrometer.setVoltage(0)
electrometer.close()