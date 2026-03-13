#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCA9548A I2C Multiplexer Controller

Reusable module for controlling the PCA9548A I2C multiplexer.
Use this to manage multiple I2C devices with the same address.

Example:
    from components.sensors.pca9548a_mux import PCA9548A
    
    # Initialize multiplexer
    mux = PCA9548A()
    
    # Select channel 0 for first sensor
    mux.select_channel(0)
    sensor1 = VL53L0XSensor()
    
    # Select channel 1 for second sensor
    mux.select_channel(1)
    sensor2 = VL53L0XSensor()
    
    # Disable all channels when done
    mux.select_channel(None)
"""

import smbus
import time


class PCA9548A:
    """
    Controller for PCA9548A I2C multiplexer.
    
    The PCA9548A allows up to 8 I2C devices or buses to be connected to a
    single I2C port. This is useful when you have multiple devices with the
    same I2C address (like multiple VL53L0X sensors at 0x29).
    
    Attributes:
        bus: SMBus instance for I2C communication
        address: Multiplexer I2C address (0x70-0x77)
        current_channel: Currently active channel (0-7 or None)
    """
    
    def __init__(self, bus_number=1, address=0x70):
        """
        Initialize multiplexer controller.
        
        Args:
            bus_number (int): I2C bus number (default 1 for Raspberry Pi)
            address (int): Multiplexer I2C address (default 0x70)
                          Can be 0x70-0x77 depending on A0-A2 pins
        
        Raises:
            IOError: If multiplexer is not found at the specified address
        """
        self.bus = smbus.SMBus(bus_number)
        self.address = address
        self.current_channel = None
        
        # Verify multiplexer is present
        try:
            self.bus.read_byte(self.address)
        except OSError:
            raise IOError(f"PCA9548A not found at address 0x{address:02X}")
        
        # Disable all channels on initialization
        self.select_channel(None)
        
    def select_channel(self, channel):
        """
        Select a single channel (0-7) on the multiplexer.
        
        Args:
            channel (int or None): Channel number 0-7, or None to disable all
        
        Raises:
            ValueError: If channel is not in valid range
            
        Example:
            mux.select_channel(0)    # Enable channel 0
            mux.select_channel(None) # Disable all channels
        """
        if channel is None:
            # Disable all channels
            self.bus.write_byte(self.address, 0x00)
            self.current_channel = None
        elif 0 <= channel <= 7:
            # Enable specific channel (bit shift: 1<<0=0x01, 1<<1=0x02, etc.)
            control_byte = 1 << channel
            self.bus.write_byte(self.address, control_byte)
            self.current_channel = channel
        else:
            raise ValueError(f"Channel must be 0-7 or None, got {channel}")
    
    def enable_multiple_channels(self, channels):
        """
        Enable multiple channels simultaneously.
        
        Args:
            channels (list): List of channel numbers to enable
            
        Example:
            mux.enable_multiple_channels([0, 1, 2])  # Enable channels 0, 1, and 2
        """
        if not channels:
            self.select_channel(None)
            return
        
        control_byte = 0
        for channel in channels:
            if 0 <= channel <= 7:
                control_byte |= (1 << channel)
            else:
                raise ValueError(f"Channel must be 0-7, got {channel}")
        
        self.bus.write_byte(self.address, control_byte)
        self.current_channel = channels[0] if len(channels) == 1 else None
    
    def get_active_channels(self):
        """
        Read which channel(s) are currently enabled.
        
        Returns:
            list: List of active channel numbers (0-7)
            
        Example:
            channels = mux.get_active_channels()
            print(f"Active: {channels}")  # e.g., [0, 2]
        """
        control_byte = self.bus.read_byte(self.address)
        active = []
        for i in range(8):
            if control_byte & (1 << i):
                active.append(i)
        return active
    
    def scan_channel(self, channel):
        """
        Scan for I2C devices on a specific channel.
        
        Args:
            channel (int): Channel number 0-7
            
        Returns:
            list: List of I2C addresses found on this channel
            
        Example:
            devices = mux.scan_channel(0)
            print(f"Found: {[hex(d) for d in devices]}")
        """
        self.select_channel(channel)
        time.sleep(0.01)  # Small delay for channel switch
        
        devices = []
        for addr in range(0x03, 0x78):
            if addr == self.address:
                continue  # Skip the multiplexer itself
            
            try:
                self.bus.read_byte(addr)
                devices.append(addr)
            except OSError:
                pass
        
        return devices
    
    def scan_all_channels(self):
        """
        Scan all 8 channels for connected devices.
        
        Returns:
            dict: Dictionary with channel numbers as keys and device lists as values
            
        Example:
            results = mux.scan_all_channels()
            # {0: [0x29], 1: [0x29], 2: [0x3C]}
        """
        results = {}
        for channel in range(8):
            devices = self.scan_channel(channel)
            if devices:
                results[channel] = devices
        
        # Disable all channels when done
        self.select_channel(None)
        return results
    
    def close(self):
        """
        Close the I2C bus and disable all channels.
        
        Call this when you're done using the multiplexer.
        """
        self.select_channel(None)  # Disable all channels
        self.bus.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures channels are disabled"""
        self.close()
        return False


# Convenience function for quick channel selection
def with_channel(mux, channel):
    """
    Context manager for automatic channel selection and cleanup.
    
    Args:
        mux: PCA9548A instance
        channel: Channel number to select
        
    Example:
        mux = PCA9548A()
        
        with with_channel(mux, 0):
            # Channel 0 is active here
            distance = sensor1.read()
        # Channel is automatically disabled after block
    """
    class ChannelSelector:
        def __enter__(self):
            mux.select_channel(channel)
            return mux
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            mux.select_channel(None)
            return False
    
    return ChannelSelector()


if __name__ == "__main__":
    print("PCA9548A Multiplexer Module")
    print("Use pca9548a_diagnostic.py for testing")
    print("Import this module to use in your code:")
    print()
    print("  from components.sensors.pca9548a_mux import PCA9548A")
    print()
