/**
 * Script to generate TypeScript types from JSON schemas
 */

import fs from 'fs/promises';
import path from 'path';
import { SchemaValidator } from '../api-schema-validator';

async function generateTypesFromSchemas() {
  console.log('🚀 Starting TypeScript type generation from schemas...');
  
  const validator = new SchemaValidator();
  const examplesDir = path.join(__dirname, '.'); // In the examples directory
  const outputDir = path.join(__dirname, '..'); // Output to parent directory
  
  try {
    // Read all JSON schema files
    const files = await fs.readdir(examplesDir);
    const schemaFiles = files.filter(file => file.endsWith('.schema.json'));
    
    if (schemaFiles.length === 0) {
      console.log('❌ No schema files found. Looking for files ending with ".schema.json"');
      return;
    }
    
    console.log(`📋 Found ${schemaFiles.length} schema files:`, schemaFiles);
    
    // Process each schema file
    for (const schemaFile of schemaFiles) {
      console.log(`\n📝 Processing ${schemaFile}...`);
      
      try {
        // Read the schema file
        const schemaPath = path.join(examplesDir, schemaFile);
        const schemaContent = await fs.readFile(schemaPath, 'utf-8');
        const schema = JSON.parse(schemaContent);
        
        // Extract contract name from filename
        const contractName = schemaFile.replace('.schema.json', '');
        
        // Create a contract wrapper
        const contract = {
          name: contractName,
          version: schema.version || '1.0.0',
          baseUrl: schema.baseUrl,
          endpoints: schema.endpoints || {}
        };
        
        // Register the contract
        validator.registerContract(contract);
        
        // Generate TypeScript types for the contract
        const tsCode = validator.generateTypesFromContract(contractName);
        
        // Write to output file
        const outputFileName = schemaFile.replace('.schema.json', '.types.ts');
        const outputPath = path.join(outputDir, outputFileName);
        
        await fs.writeFile(outputPath, tsCode);
        console.log(`✅ Generated types to ${outputFileName}`);
        
      } catch (error) {
        console.error(`❌ Error processing ${schemaFile}:`, error);
      }
    }
    
    // Also generate a combined types file
    console.log('\n📦 Generating combined types file...');
    const allContracts = Array.from(validator['contracts'].keys());
    if (allContracts.length > 0) {
      const combinedTypes = [];
      combinedTypes.push('// Combined TypeScript types from all schemas\n');
      combinedTypes.push('// Auto-generated: Do not edit manually\n');
      combinedTypes.push(`// Generated at: ${new Date().toISOString()}\n`);
      
      for (const contractName of allContracts) {
        try {
          const contractTypes = validator.generateTypesFromContract(contractName);
          combinedTypes.push(`// Types from contract: ${contractName}\n`);
          combinedTypes.push(contractTypes);
          combinedTypes.push('\n');
        } catch (error) {
          console.error(`❌ Error generating types for ${contractName}:`, error);
        }
      }
      
      const combinedOutputPath = path.join(outputDir, 'api-contracts.types.ts');
      await fs.writeFile(combinedOutputPath, combinedTypes.join('\n'));
      console.log(`✅ Generated combined types to api-contracts.types.ts`);
    }
    
    console.log('\n🎉 TypeScript type generation completed successfully!');
    
  } catch (error) {
    console.error('❌ Error during type generation:', error);
    process.exit(1);
  }
}

// Run the script if called directly
if (require.main === module) {
  generateTypesFromSchemas().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

export { generateTypesFromSchemas };