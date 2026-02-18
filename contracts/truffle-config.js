/**
 * Truffle Configuration for Verif-AI Blockchain
 * 
 * Configures network connections and compiler settings for smart contract deployment.
 */

module.exports = {
  // Contracts directory
  contracts_directory: "./contracts",
  contracts_build_directory: "./build/contracts",
  
  // Network configurations
  networks: {
    // Ganache network (for npm scripts)
    ganache: {
      host: "127.0.0.1",
      port: 7545,           // Ganache GUI default port (use 8545 for CLI)
      network_id: 5777,     // Ganache default network_id
      gas: 6721975,         // Gas limit
      gasPrice: 20000000000 // 20 gwei
    },
    
    // Local Ganache development network
    development: {
      host: "127.0.0.1",
      port: 7545,           // Ganache GUI default port
      network_id: "*",      // Match any network id
      gas: 6721975,         // Gas limit
      gasPrice: 20000000000 // 20 gwei
    },
    
    // Ganache CLI (if using CLI instead of GUI)
    ganache_cli: {
      host: "127.0.0.1",
      port: 8545,           // Ganache CLI default port
      network_id: "*",
      gas: 6721975,
      gasPrice: 20000000000
    }
  },

  // Compiler configuration
  compilers: {
    solc: {
      version: "0.8.19",    // Solidity version
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        },
        evmVersion: "paris"
      }
    }
  },

  // Plugin configuration (if using plugins)
  plugins: [],

  // Mocha testing configuration
  mocha: {
    timeout: 120000  // 2 minutes only
  }
};
