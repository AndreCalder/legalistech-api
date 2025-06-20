📓 Changelog — Multi-Tool Function Call Execution (Pinecone + Mongo)
📅 Date: 06/06/2025

✅ Added

AssistantController.py now supports handling multiple function_calls from Gemini in a single response.

Introduced loop logic to iterate over response.candidates[0].function_calls and handle each call independently.

Implemented conditional branching by source (either "pinecone" or "mongo_sentencias"), ensuring proper tool dispatch.

Built cumulative response body (tool_result_text) aggregating results from all tool calls.

Added debug_log tracking execution time for each tool call individually.

Added support for multiple law article searches (combined_legal_search with source "pinecone"), one per article.

Added support for multiple case-type searches (combined_legal_search with source "mongo_sentencias"), one per case type.

Consolidated tool outputs into a single message injected into the model’s context for follow-up generation.

Adjusted final prompt to include tool results instead of FILE_DATA, when appropriate.

Maintained modular structure for future scalability (e.g. new tools or routing logic).

🛠 Files changed

controllers/assistantController.py: core logic for multi-call loop and aggregation.

controllers/util/assistant_config.py: system instructions now explicitly support multi-article and multi-case detection with looping function calls.

📎 Additional notes

The model now handles compound user queries such as:
“What do articles 27, 123, and 145 say?” or
“Show me favorable rulings in family disputes and intestate successions.”

No changes made to database schema or public-facing API routes.

Equivalent logic still pending for the specialized mongo_sentencias model configuration.

--------------------------------------

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