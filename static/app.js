document.addEventListener('DOMContentLoaded', () => {

    const slides = document.querySelectorAll('.slide');
    const wizardCard = document.getElementById('wizard-card');
    const resultsCard = document.getElementById('results-card');
    
    // --- Navigation Functions ---
    function showSlide(slideId) {
        slides.forEach(s => {
            s.classList.remove('active-slide');
            s.classList.add('hidden-slide');
        });
        document.getElementById(slideId).classList.remove('hidden-slide');
        document.getElementById(slideId).classList.add('active-slide');
    }

    // --- Global User State ---
    let currentUser = null;

    // --- Home / Slide 0 Routing ---
    document.getElementById('go-login-btn').addEventListener('click', () => {
        document.getElementById('wizard-subtitle').textContent = "Welcome back.";
        showSlide('slide-login');
    });

    document.getElementById('go-signup-btn').addEventListener('click', () => {
        document.getElementById('wizard-subtitle').textContent = "Step 1 of 3: Credentials";
        showSlide('slide-signup-1');
    });

    document.querySelectorAll('.back-to-home').forEach(btn => {
        btn.addEventListener('click', () => {
            currentUser = null;
            document.getElementById('wizard-subtitle').textContent = "Your personal AI nutritionist.";
            showSlide('slide-0');
        });
    });

    // --- Dashboard Routing ---
    document.getElementById('btn-new-plan').addEventListener('click', () => {
        document.getElementById('wizard-subtitle').textContent = "Step 2 of 3: Macros (Part 1)";
        showSlide('slide-signup-2');
    });

    document.getElementById('btn-view-history').addEventListener('click', async () => {
        if (!currentUser) return;
        document.getElementById('wizard-subtitle').textContent = "Past Meal Plans";
        showSlide('slide-history');
        
        try {
            const res = await fetch(`/api/history/${currentUser.id}`);
            const data = await res.json();
            const container = document.getElementById('history-container');
            if (data.history && data.history.length > 0) {
                container.innerHTML = data.history.map(item => `
                    <div style="background: var(--bg-panel); border: 1px solid var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <div style="font-size: 0.8rem; color: var(--primary); margin-bottom: 0.5rem;">Created: ${new Date(item.created_at).toLocaleString()}</div>
                        <div class="markdown-body">${marked.parse(item.plan_content)}</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p>No past meal plans found.</p>';
            }
        } catch (e) {
            console.error(e);
            document.getElementById('history-container').innerHTML = '<p>Error loading history.</p>';
        }
    });

    document.getElementById('back-to-dashboard-from-history').addEventListener('click', () => {
        document.getElementById('wizard-subtitle').textContent = "What would you like to do today?";
        showSlide('slide-dashboard');
    });

    // --- Signup Flow ---
    document.getElementById('next-signup-1').addEventListener('click', () => {
        if (!document.getElementById('signup-name').value || !document.getElementById('signup-password').value) {
            return alert("Please enter a username and password.");
        }
        document.getElementById('wizard-subtitle').textContent = "Step 2 of 3: Macros (Part 1)";
        showSlide('slide-signup-2');
    });

    document.getElementById('prev-signup-2').addEventListener('click', () => {
        document.getElementById('wizard-subtitle').textContent = "Step 1 of 3: Credentials";
        showSlide('slide-signup-1');
    });

    document.getElementById('next-signup-2').addEventListener('click', () => {
        if (!document.getElementById('calories').value || !document.getElementById('protein').value) {
            return alert("Please fill in your calories and protein.");
        }
        document.getElementById('wizard-subtitle').textContent = "Step 3 of 3: Macros (Part 2)";
        showSlide('slide-signup-3');
    });

    document.getElementById('prev-signup-3').addEventListener('click', () => {
        document.getElementById('wizard-subtitle').textContent = "Step 2 of 3: Macros (Part 1)";
        showSlide('slide-signup-2');
    });


    // --- Global Generation Call ---
    async function executeGeneration(userId, userName, cuisine) {
        try {
            const queryInput = `I want a structured ${cuisine} meal plan based on my nutritional targets.`;
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, query: queryInput })
            });

            if (!response.ok) throw new Error("Meal plan generation failed.");
            
            const result = await response.json();
            
            wizardCard.classList.add('hidden');
            resultsCard.classList.remove('hidden');
            document.getElementById('user-greeting').textContent = `Hi ${userName}, here is your ${cuisine} meal plan!`;
            document.getElementById('meal-plan-content').innerHTML = marked.parse(result.meal_plan);

        } catch (error) {
            console.error(error);
            alert("API Error: " + error.message);
            throw error;
        }
    }


    // --- Login Submission ---
    document.getElementById('submit-login-btn').addEventListener('click', async () => {
        const name = document.getElementById('login-name').value;
        const pwd = document.getElementById('login-password').value;
        if (!name || !pwd) return alert("Enter credentials.");

        const btnText = document.querySelector('#submit-login-btn .btn-text');
        const loader = document.getElementById('login-loader');
        
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, password: pwd })
            });

            if (!res.ok) throw new Error("Invalid username or password.");
            const data = await res.json();
            
            // Set current user and go to dashboard
            currentUser = { id: data.user_id, name: data.name };
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            
            document.getElementById('wizard-subtitle').textContent = "What would you like to do today?";
            showSlide('slide-dashboard');

        } catch (error) {
            alert(error.message);
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });


    // --- Signup Submission ---
    document.getElementById('submit-signup-btn').addEventListener('click', async () => {
        if (!document.getElementById('carbs').value || !document.getElementById('fiber').value || !document.getElementById('sugar_limit').value) {
            return alert("Please fill all macro targets.");
        }

        const formData = new FormData(document.getElementById('wizard-form'));
        const profileData = Object.fromEntries(formData.entries());
        
        // Convert to ints
        profileData.calories = parseInt(profileData.calories) || 2000;
        profileData.protein = parseInt(profileData.protein) || 150;
        profileData.fat = parseInt(profileData.fat) || 65;
        profileData.carbs = parseInt(profileData.carbs) || 200;
        profileData.fiber = parseInt(profileData.fiber) || 30;
        profileData.sugar_limit = parseInt(profileData.sugar_limit) || 40;
        profileData.sodium = parseInt(profileData.sodium) || 2300;
        profileData.cholesterol = parseInt(profileData.cholesterol) || 300;

        // New inputs
        profileData.meals_per_day = profileData.meals_per_day || "3 Meals";
        profileData.plan_duration = profileData.plan_duration || "1 Day";

        const btnText = document.querySelector('#submit-signup-btn .btn-text');
        const loader = document.getElementById('signup-loader');
        
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');

        try {
            // If the user is already logged in (coming from dashboard), we don't strictly need to create a new user row,
            // but for simplicity we'll create a new profile iteration or just proceed to generation.
            // Since the API requires user_id, let's check if logged in.
            
            let finalUserId = currentUser ? currentUser.id : null;
            let finalUserName = profileData.name || (currentUser ? currentUser.name : "User");

            if (!currentUser) {
                // New User Creation
                const res = await fetch('/api/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(profileData)
                });

                if (!res.ok) throw new Error("Could not create account.");
                const data = await res.json();
                finalUserId = data.user_id;
                currentUser = { id: finalUserId, name: finalUserName }; // Log them in
            } else {
                // Update Existing User Profile in Database
                profileData.name = currentUser.name;
                // Add dummy password if missing, DB update_user_profile excludes name but expects proper schema
                profileData.password = document.getElementById('signup-password').value || 'temp_pass'; 
                
                const res = await fetch(`/api/users/${currentUser.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(profileData)
                });
                
                if (!res.ok) throw new Error("Could not update profile.");
            }
            
            await executeGeneration(finalUserId, finalUserName, profileData.cuisine_type);

        } catch (error) {
            alert(error.message);
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });

});
