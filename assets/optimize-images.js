#!/usr/bin/env node

const imagemin = require('imagemin').default;
const path = require('path');
const fs = require('fs');

const inputDir = path.join(__dirname, 'static', 'images');
const outputDir = path.join(__dirname, '..', 'public', 'images');

// Ensure output directory exists
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

async function copyImages() {
  console.log('🖼️  Copying images to public directory...');
  console.log(`📁 Input: ${inputDir}`);
  console.log(`📁 Output: ${outputDir}`);

  try {
    const files = await imagemin(
      [`${inputDir}/**/*.{jpg,jpeg,png}`, `${inputDir}/*.{jpg,jpeg,png}`],
      {
        destination: outputDir,
        plugins: [],
      }
    );

    console.log(`✅ Copied ${files.length} images:`);
    files.forEach(file => {
      const relativePath = path.relative(outputDir, file.destinationPath);
      const fileSize = fs.statSync(file.destinationPath).size;
      console.log(`   ${relativePath}: ${(fileSize / 1024).toFixed(1)}KB`);
    });

    console.log('🎉 Image copy complete!');
  } catch (error) {
    console.error('❌ Error copying images:', error);
    process.exit(1);
  }
}

copyImages();
