document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('three-canvas');
    if (!canvas) return;

    if (typeof THREE === 'undefined') {
        console.error('Three.js is not loaded.');
        return;
    }

    // --- 1. SETUP ENGINE ---
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050508, 0.02); // Deep rich dark background

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;

    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 45); // Centered, looking straight on

    // --- 2. LIGHTING ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    const cyanLight = new THREE.PointLight(0x00f0ff, 4, 60);
    cyanLight.position.set(-10, 5, 5);
    scene.add(cyanLight);

    const purpleLight = new THREE.PointLight(0x8b5cf6, 4, 60);
    purpleLight.position.set(10, -5, 5);
    scene.add(purpleLight);

    // --- 3. PREMIUM ABSTRACT DATA STREAM (LEFT TO RIGHT) ---
    // Instead of clunky geometric parts, we use a massive flowing particle river
    const particleCount = 4000;
    const streamGeom = new THREE.BufferGeometry();
    const streamPos = new Float32Array(particleCount * 3);
    const streamSpeeds = new Float32Array(particleCount);
    
    for(let i=0; i<particleCount; i++) {
        streamPos[i*3] = -40 + Math.random() * 80; // X spread across screen
        streamPos[i*3+1] = (Math.random() - 0.5) * 10; // Y spread (tighter river)
        streamPos[i*3+2] = (Math.random() - 0.5) * 15; // Z depth
        
        streamSpeeds[i] = 0.05 + Math.random() * 0.1; // Speed flowing right
    }
    streamGeom.setAttribute('position', new THREE.BufferAttribute(streamPos, 3));
    streamGeom.setAttribute('speed', new THREE.BufferAttribute(streamSpeeds, 1));
    
    // Create a glowing, additive blended material for the data stream
    const streamMat = new THREE.PointsMaterial({
        size: 0.15,
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });
    const dataStream = new THREE.Points(streamGeom, streamMat);
    scene.add(dataStream);

    // --- 4. CENTER: INTELLIGENCE NEXUS (THE CORE) ---
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Inner glowing sphere (Massive)
    const coreInnerGeom = new THREE.IcosahedronGeometry(12, 3);
    const coreInnerMat = new THREE.MeshStandardMaterial({
        color: 0x8b5cf6, // Deep Purple
        wireframe: true,
        transparent: true,
        opacity: 0.05,
        blending: THREE.AdditiveBlending
    });
    const coreInner = new THREE.Mesh(coreInnerGeom, coreInnerMat);
    coreGroup.add(coreInner);

    // Outer wireframe cage (Massive)
    const coreOuterGeom = new THREE.IcosahedronGeometry(12.5, 1);
    const coreOuterMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        wireframe: true,
        transparent: true,
        opacity: 0.08,
        blending: THREE.AdditiveBlending
    });
    const coreOuter = new THREE.Mesh(coreOuterGeom, coreOuterMat);
    coreGroup.add(coreOuter);

    // --- 5. RIGHT SIDE: PERFECTED DATA CONSTRUCT (REMOVED) ---
    // Removed per user request.


    // --- 6. ANIMATION LOOP ---
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        const time = clock.getElapsedTime();

        // 1. Flow the Data Stream
        const positions = dataStream.geometry.attributes.position.array;
        const speeds = dataStream.geometry.attributes.speed.array;
        
        for(let i=0; i<particleCount; i++) {
            positions[i*3] += speeds[i]; // Move right
            
            // Add a slight sine wave flutter to Y for a fluid look
            positions[i*3+1] += Math.sin(time * 2 + positions[i*3]) * 0.01;

            // Loop back to the left side if they go too far right
            if (positions[i*3] > 40) {
                positions[i*3] = -40;
            }
        }
        dataStream.geometry.attributes.position.needsUpdate = true;

        // 2. Animate the Nexus Core
        coreGroup.rotation.y = time * 0.1;
        coreGroup.rotation.z = time * 0.05;
        coreInner.scale.setScalar(1 + Math.sin(time * 3) * 0.02); // Subtle pulse

        // 3. Animate the Perfected Output (Removed)

        renderer.render(scene, camera);
    }

    function resizeCanvas() {
        renderer.setSize(window.innerWidth, window.innerHeight);
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
    }
    window.addEventListener('resize', resizeCanvas);

    // Fade out loader instantly since procedural
    const loader = document.getElementById('loading-manager');
    if(loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.style.display = 'none', 500);
    }

    animate();
});
