/**
 * Truffle Configuration for Verif-AI Contracts
 * 
 * Configured for local Ganache development by default.
 * 
 * SETUP:
 * 1. Install Ganache: https://trufflesuite.com/ganache/
 * 2. Start Ganache on port 7545 (default)
 * 3. Run: npm run deploy
 */

module.exports = {
  /**
   * Networks define how you connect to your ethereum client.
   */
  networks: {
    // Local Ganache development network
    ganache: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*", // Match any network id
      gas: 6721975,    // Ganache default gas limit
      gasPrice: 20000000000, // 20 gwei
    },

    // Ganache CLI (if using ganache-cli instead of GUI)
    ganache_cli: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*",
    },

    // Development network (alias for ganache)
    development: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*",
    },
  },

  // Configure compilers
  compilers: {
    solc: {
      version: "0.8.19",
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        },
        evmVersion: "paris"
      }
    }
  },

  // Truffle DB (disabled for performance)
  db: {
    enabled: false
  },

  // Mocha testing configuration
  mocha: {
    timeout: 100000
  },

  // Plugin configurations
  plugins: []
};
