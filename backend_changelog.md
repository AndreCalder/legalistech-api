📓 Changelog — Account Verification via PIN Integration
📅 Date: 2025-05-20

✅ Added
🔐 PIN generation & storage:

Added controllers/pins_controller.py with:

generate_pin_for_user(user_id) → creates and stores a 4-digit PIN

verify_user_pin(user_id, pin_code) → validates the PIN, marks it used, and sets confirmed_acc

Defined users = db["users"] and pins = db["pins"] via mongoConnection.db

Created pins collection documents with fields:

user_id as ObjectId

pin_code as string

created_at timestamp

PIN_used boolean

🌐 PIN API routes:

Added routes/pins_blueprint.py with:

POST /pins/ → generate PIN

POST /pins/verify → verify PIN

Registered pins_bp under /pins in routes/router.py

🛠️ UserController update:

In controllers/userController.py#create_user, after inserting a new user:

Generate a 4-digit PIN and insert into pins collection

Return JSON { "userId": ..., "pin_code": ... } (status 201)

🛠️ Changed
🔄 Auth flow update:

Refactored AuthController and authBlueprint to use email instead of username

Updated error messages to “Email or password is incorrect”

Token payload now contains "email" rather than "username"

⚙️ Blueprint consistency:

Ensured authBlueprint reads email field and calls authController.login(email, password)

📝 Commit
feat(auth): implement PIN-based account verification and refactor login to use email📓 Changelog — Account Verification via PIN Integration
📅 Date: 2025-05-20

✅ Added
🔐 PIN generation & storage:

Added controllers/pins_controller.py with:

generate_pin_for_user(user_id) → creates and stores a 4-digit PIN

verify_user_pin(user_id, pin_code) → validates the PIN, marks it used, and sets confirmed_acc

Defined users = db["users"] and pins = db["pins"] via mongoConnection.db

Created pins collection documents with fields:

user_id as ObjectId

pin_code as string

created_at timestamp

PIN_used boolean

🌐 PIN API routes:

Added routes/pins_blueprint.py with:

POST /pins/ → generate PIN

POST /pins/verify → verify PIN

Registered pins_bp under /pins in routes/router.py

🛠️ UserController update:

In controllers/userController.py#create_user, after inserting a new user:

Generate a 4-digit PIN and insert into pins collection

Return JSON { "userId": ..., "pin_code": ... } (status 201)

🛠️ Changed
🔄 Auth flow update:

Refactored AuthController and authBlueprint to use email instead of username

Updated error messages to “Email or password is incorrect”

Token payload now contains "email" rather than "username"

⚙️ Blueprint consistency:

Ensured authBlueprint reads email field and calls authController.login(email, password)

📝 Commit
feat(auth): implement PIN-based account verification and refactor login to use email