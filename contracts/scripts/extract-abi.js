/**
 * Extract ABI from compiled contract for backend use
 * 
 * Run: node scripts/extract-abi.js
 */

const fs = require('fs');
const path = require('path');

const buildPath = path.join(__dirname, '..', 'build', 'contracts', 'AnalysisAnchor.json');
const outputPath = path.join(__dirname, '..', '..', 'backend', 'src', 'infrastructure', 'blockchain', 'abi');

try {
  // Read compiled contract
  const contractJson = JSON.parse(fs.readFileSync(buildPath, 'utf8'));
  
  // Extract ABI
  const abi = contractJson.abi;
  
  // Ensure output directory exists
  if (!fs.existsSync(outputPath)) {
    fs.mkdirSync(outputPath, { recursive: true });
  }
  
  // Write ABI file
  const abiPath = path.join(outputPath, 'AnalysisAnchor.json');
  fs.writeFileSync(abiPath, JSON.stringify(abi, null, 2));
  
  console.log('✅ ABI extracted successfully!');
  console.log(`   Output: ${abiPath}`);
  console.log(`   Functions: ${abi.filter(x => x.type === 'function').length}`);
  console.log(`   Events: ${abi.filter(x => x.type === 'event').length}`);
  
} catch (error) {
  if (error.code === 'ENOENT') {
    console.error('❌ Contract not compiled yet. Run: npm run compile');
  } else {
    console.error('❌ Error:', error.message);
  }
  process.exit(1);
}
