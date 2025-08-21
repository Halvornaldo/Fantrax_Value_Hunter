// v2.0 Parameter Controls Verification Script
// Run this in browser console when dashboard is loaded

console.log('🧪 Starting v2.0 Parameter Controls Verification...');

// Test 1: Check if v2.0 enhanced sections exist
function testV2SectionsExist() {
    const v2Sections = document.querySelectorAll('.v2-enhanced-section');
    console.log(`✅ Found ${v2Sections.length} v2.0 enhanced sections`);
    
    const expectedSections = [
        'EWMA Form Calculation',
        'Dynamic Blending Controls', 
        'Normalized xGI Controls',
        'Multiplier Cap Controls'
    ];
    
    expectedSections.forEach((sectionName, index) => {
        if (v2Sections[index]) {
            console.log(`  ✓ ${sectionName} section found`);
        } else {
            console.error(`  ✗ ${sectionName} section missing`);
        }
    });
}

// Test 2: Verify EWMA calculation function
function testEWMACalculation() {
    console.log('\n📊 Testing EWMA Half-life Calculation:');
    const testValues = [0.1, 0.5, 0.87, 0.95];
    
    testValues.forEach(alpha => {
        const halfLife = Math.log(0.5) / Math.log(1 - alpha);
        console.log(`  α=${alpha} → Half-life=${halfLife.toFixed(1)} games`);
    });
}

// Test 3: Verify dynamic blending calculation
function testBlendingCalculation() {
    console.log('\n🔀 Testing Dynamic Blending Weights:');
    const adaptationGameweek = 15;
    const testGameweeks = [1, 5, 10, 15, 20];
    
    testGameweeks.forEach(gameweek => {
        const currentWeight = Math.min(1, (gameweek - 1) / (adaptationGameweek - 1));
        const historicalWeight = 1 - currentWeight;
        console.log(`  GW${gameweek} (K=${adaptationGameweek}): Current=${(currentWeight*100).toFixed(0)}%, Historical=${(historicalWeight*100).toFixed(0)}%`);
    });
}

// Test 4: Check if v2.0 controls are properly initialized
function testV2ControlsInitialization() {
    console.log('\n🎛️ Testing v2.0 Controls Initialization:');
    
    const controls = [
        'ewma-alpha-slider',
        'adaptation-gameweek-input',
        'xgi-normalization-strength',
        'form-cap-slider',
        'fixture-cap-slider',
        'xgi-cap-slider',
        'global-cap-slider'
    ];
    
    controls.forEach(controlId => {
        const element = document.getElementById(controlId);
        if (element) {
            console.log(`  ✓ ${controlId}: ${element.type} with value ${element.value}`);
        } else {
            console.error(`  ✗ ${controlId}: Element not found`);
        }
    });
}

// Test 5: Verify parameter collection function
function testParameterCollection() {
    console.log('\n📋 Testing v2.0 Parameter Collection:');
    
    try {
        if (typeof collectV2Parameters === 'function') {
            const params = collectV2Parameters();
            console.log('  ✓ collectV2Parameters() executed successfully');
            console.log('  📊 Collected parameters:', params);
            
            // Validate structure
            const requiredKeys = ['ewma_form', 'dynamic_blending', 'normalized_xgi', 'multiplier_caps'];
            requiredKeys.forEach(key => {
                if (params[key]) {
                    console.log(`    ✓ ${key} section present`);
                } else {
                    console.error(`    ✗ ${key} section missing`);
                }
            });
        } else {
            console.error('  ✗ collectV2Parameters function not found');
        }
    } catch (error) {
        console.error('  ✗ Error collecting v2.0 parameters:', error);
    }
}

// Test 6: Check v2.0 visibility based on formula selection
function testV2Visibility() {
    console.log('\n👁️ Testing v2.0 Visibility Logic:');
    
    const formulaV2 = document.getElementById('formula-v2');
    const formulaV1 = document.getElementById('formula-v1');
    
    if (formulaV2 && formulaV1) {
        // Test v2.0 mode
        formulaV2.checked = true;
        formulaV1.checked = false;
        document.body.className = 'v2-enabled';
        
        const v2Sections = document.querySelectorAll('.v2-enhanced-section');
        const visibleSections = Array.from(v2Sections).filter(section => 
            getComputedStyle(section).display !== 'none'
        );
        
        console.log(`  v2.0 mode: ${visibleSections.length}/${v2Sections.length} sections visible`);
        
        // Test v1.0 mode
        formulaV1.checked = true;
        formulaV2.checked = false;
        document.body.className = 'v1-enabled';
        
        const hiddenSections = Array.from(v2Sections).filter(section => 
            getComputedStyle(section).display === 'none'
        );
        
        console.log(`  v1.0 mode: ${hiddenSections.length}/${v2Sections.length} sections hidden`);
        
        // Restore v2.0 mode for testing
        formulaV2.checked = true;
        formulaV1.checked = false;
        document.body.className = 'v2-enabled';
    } else {
        console.error('  ✗ Formula radio buttons not found');
    }
}

// Run all tests
function runAllTests() {
    console.log('🚀 Running Complete v2.0 Parameter Controls Test Suite\n');
    
    testV2SectionsExist();
    testEWMACalculation();
    testBlendingCalculation();
    testV2ControlsInitialization();
    testParameterCollection();
    testV2Visibility();
    
    console.log('\n✅ v2.0 Parameter Controls Verification Complete!');
    console.log('📋 Check results above for any issues');
}

// Auto-run tests after a short delay to ensure DOM is ready
setTimeout(runAllTests, 1000);