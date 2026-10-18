import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from esphome.const import CONF_ID
from . import sma_bluetooth_ns, SmaBluetoothHub, CONF_SMA_BLUETOOTH_ID

SmaInverterDevice = sma_bluetooth_ns.class_("SmaInverterDevice")

CONF_MAC_ADDRESS = "mac_address"
CONF_GRID_RELAY = "grid_relay"
CONF_INVERTER_FAULT = "inverter_fault"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(SmaInverterDevice),
        cv.GenerateID(CONF_SMA_BLUETOOTH_ID): cv.use_id(SmaBluetoothHub),
        cv.Required(CONF_MAC_ADDRESS): cv.string,
        cv.Optional(CONF_GRID_RELAY): binary_sensor.binary_sensor_schema(
            icon="mdi:transmission-tower",
        ),
        cv.Optional(CONF_INVERTER_FAULT): binary_sensor.binary_sensor_schema(
            device_class="problem",
            icon="mdi:alert-circle",
        ),
    }
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_SMA_BLUETOOTH_ID])

    var = cg.new_Pvariable(config[CONF_ID])
    cg.add(var.set_mac_address(config[CONF_MAC_ADDRESS]))
    cg.add(hub.register_device(var))

    if CONF_GRID_RELAY in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_GRID_RELAY])
        cg.add(var.set_grid_relay_sensor(sens))

    if CONF_INVERTER_FAULT in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_INVERTER_FAULT])
        cg.add(var.set_inverter_fault_sensor(sens))
