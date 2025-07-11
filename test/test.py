# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.result import TestFailure
import random

# ---------------------- This test needs to be updated to the actual project -------------------------
# 1. test using static weight, 3 sets of testing data
# 2. test using partially loaded weight onto neuron 1 & 2, 3 sets
# 3. test using fully loaded weight onto all neurons, 3 sets 
# 4. test on debugging outputs and intermediate process, 1 set
@cocotb.test()
async def test_tt_um_BNN(dut): 
    # Start clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize signals
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 0
    
    # Reset for 2 cycles
    await Timer(2, units="ns")
    dut.rst_n.value = 1
    await Timer(2, units="ns")
    
    # --------------------------
    # Test 1: Verify Hardcoded Weights
    # --------------------------
    await test_hardcoded_weights(dut)
    
    # --------------------------
    # Test 2: Dynamic Weight Loading
    # --------------------------
    # await test_weight_loading(dut)
    
    # --------------------------
    # Test 3: Full Network Inference
    # --------------------------
    # await test_network_inference(dut)

async def test_hardcoded_weights(dut):
    # Test initial hard-coded weights
    cocotb.log.info("Testing hardcoded weights")
    
    # A single test 0b11110000 is provided, more could be added later
    # Test pattern that should activate neuron 0 (weights = 11110000)
    test_input = 0b11110000
    expected_output = 0b1101  # Only first neuron of last layer should activate
    
    dut.ui_in.value = test_input
    await Timer(2, units="ns")  # Allow combinational logic to settle
    assert int(dut.uo_out.value[4:7]) == expected_output, f"Hardcoded weight test failed. Got {bin(dut.uo_out.value[4:7])}, expected {bin(expected_output)}"

async def test_weight_loading(dut):
    """Test dynamic weight loading through bidirectional pins"""
    cocotb.log.info("Testing weight loading")
    
    # Enable weight loading mode
    dut.uio_in.value = 0b00001000  # Set bit 3 (load_en) high
    
    # Test loading weights for neuron 0
    new_weights = 0b00000000
    await load_weights(dut, neuron_idx=0, weights=new_weights)
    
    # Verify by testing inference
    test_input = 0b10100101  # Should perfectly match new weights
    expected_output = 0b1000  # Threshold is 5 (0101), sum will be 8
    
    dut.ui_in.value = test_input
    dut.uio_in.value = 0  # Disable weight loading
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    assert int(dut.uo_out.value) == expected_output, f"Weight loading test failed. Got {dut.uo_out.value}, expected {expected_output}"

async def load_weights(dut, neuron_idx, weights):
    """Helper function to load weights for a specific neuron"""
    # Load lower 4 bits first
    dut.uio_in.value = (weights & 0x0F) << 4 | 0b1000
    await RisingEdge(dut.clk)
    
    # Load upper 4 bits
    dut.uio_in.value = (weights >> 4) << 4 | 0b1000
    await RisingEdge(dut.clk)

    cocotb.log.info(f"Loaded weights {bin(weights)} to neuron {neuron_idx}")

async def test_network_inference(dut):
    # Simulates the complete process using python here
    cocotb.log.info("Testing network inference")
    
    # Test 10 random patterns
    for _ in range(10):
        # Generate random input
        test_input = random.randint(0, 255)
        
        # Calculate expected output (based on hardcoded weights)
        expected = calculate_expected_output(test_input)
        
        # Apply input
        dut.ui_in.value = test_input
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        
        # Verify output
        assert int(dut.uo_out.value) == expected, f"Inference failed for input {bin(test_input)}. Got {dut.uo_out.value}, expected {expected}"

def calculate_expected_output(input_val):
    """Calculate expected output based on hardcoded weights"""
    # Layer 1 weights (first 8 neurons)
    layer1_weights = [
        0b11110000, 0b00001111, 0b00111100, 0b11000011,
        0b11110000, 0b00001111, 0b00111100, 0b11000011
    ]
    
    # Layer 2 weights (neurons 8-11)
    layer2_weights = [
        0b11110000, 0b00001111, 0b00111100, 0b11000011
    ]
    
    # Layer 3 weights (neurons 12-15)
    layer3_weights = [
        0b11110000, 0b00110000, 0b10100000, 0b11000011
    ]
    
    # Threshold for all neurons is 5 (0101)
    threshold = 5
    
    # Layer 1 computation
    layer1_output = 0
    for i in range(8):
        matches = bin(input_val ^ layer1_weights[i]).count('0')
        if matches >= threshold:
            layer1_output |= (1 << i)
    
    # Layer 2 computation
    layer2_output = 0
    for i in range(4):
        # Compare with bits [4:7] of weights (per your code)
        weight_part = (layer2_weights[i] >> 4) & 0x0F
        input_part = (layer1_output >> 4) & 0x0F
        matches = bin(input_part ^ weight_part).count('0')
        if matches >= threshold:
            layer2_output |= (1 << i)
    
    # Layer 3 computation
    final_output = 0
    for i in range(4):
        # Compare with bits [4:7] of weights (per your code)
        weight_part = (layer3_weights[i] >> 4) & 0x0F
        input_part = layer2_output
        matches = bin(input_part ^ weight_part).count('0')
        if matches >= threshold:
            final_output |= (1 << i)
    
    return final_output