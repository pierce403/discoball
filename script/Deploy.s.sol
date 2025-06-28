// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script, console} from "forge-std/Script.sol";
import {DiscoBallRegistry} from "../src/DiscoBallRegistry.sol";

contract DeployScript is Script {
    function setUp() public {}

    function run() public {
        // Get deployer private key from environment
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);

        // Deploy the DiscoBallRegistry contract
        DiscoBallRegistry registry = new DiscoBallRegistry();
        
        console.log("DiscoBallRegistry deployed to:", address(registry));
        
        // Stop broadcasting
        vm.stopBroadcast();
        
        // Log some useful information
        console.log("Deployment complete!");
        console.log("Contract address:", address(registry));
        console.log("Deployer:", vm.addr(deployerPrivateKey));
    }
} 