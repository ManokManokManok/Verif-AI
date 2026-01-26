const AnalysisAnchor = artifacts.require("AnalysisAnchor");

module.exports = async function (deployer, network, accounts) {
  console.log("=".repeat(60));
  console.log("Deploying AnalysisAnchor Contract");
  console.log("=".repeat(60));
  console.log(`Network: ${network}`);
  console.log(`Deployer account: ${accounts[0]}`);
  console.log("");

  // Deploy the contract
  await deployer.deploy(AnalysisAnchor);
  
  const instance = await AnalysisAnchor.deployed();
  
  console.log("");
  console.log("=".repeat(60));
  console.log("Deployment Successful!");
  console.log("=".repeat(60));
  console.log(`Contract Address: ${instance.address}`);
  console.log(`Owner Address:    ${await instance.owner()}`);
  console.log("");
  console.log("Save these values for backend configuration:");
  console.log(`  CHAIN_CONTRACT_ADDRESS=${instance.address}`);
  console.log("");
};
