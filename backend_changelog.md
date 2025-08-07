📓 Changelog — Password Reset + Mandrill Email Integration  
📅 Date: 2025-08-07

✅ Added

🔐 Password reset via JWT token (30 min expiration)  
- Token creation uses `RESET_TOKEN_SECRET` stored in `.env`.  
- Token saved in MongoDB collection `password_reset_tokens` with fields:
  - `token`
  - `user_id`
  - `used`
  - `created_at`
  - `expires_at`
- Two endpoints added to `authBlueprint`:
  - `POST /auth/requestReset`
    - Body: `{ "email": "..." }`
    - Generates reset token if user exists.
  - `POST /auth/resetPassword`
    - Body: `{ "token": "...", "new_password": "..." }`
    - Verifies token and updates password.

🧪 Password validation improvements  
- Added bcrypt comparison in `verify_and_reset_password` to prevent reusing current password.

🛠️ TokenController updates  
- New methods:
  - `find_user_by_email(email)`
  - Updated `verify_and_reset_password(...)` to check token validity and current password reuse.
- Reuses `_create_token()` internally for password reset token.

📤 Migrated email sending to Mandrill (Mailchimp Transactional)  
- `email_utils.py` refactored to use `requests.post(...)` with Mandrill API:
  - Uses endpoint: `https://mandrillapp.com/api/1.0/messages/send.json`
  - Requires `.env` variable: `MAILCHIMP_TRANSACTIONAL_KEY`
  - Uses `MAIL_DEFAULT_SENDER` and `MAILCHIMP_ADMIN_NOTIFY_EMAIL` for from/reply

- Two email functions updated:
  - `send_pin_email(to_email, pin_code, user_id)`
  - `notify_admin_new_contact(name, last_name, email, phone, message_text)`

🧪 Postman test coverage  
- `/auth/requestReset` → returns token if user exists  
- `/auth/resetPassword` → resets password if token valid and unused  
- `/contact/contact` → adds contact to Mailchimp and sends transactional email  
- `/pins/` → sends PIN email to user using Mandrill  

🧩 Other changes  
- `.env` updated with:
  RESET_TOKEN_SECRET=...
  MAILCHIMP_TRANSACTIONAL_KEY=...
  MAIL_DEFAULT_SENDER=notificaciones@milegalistech.ai
  MAILCHIMP_ADMIN_NOTIFY_EMAIL=soporte@milegalistech.ai

- `email_config.py` is now deprecated for SMTP-based config, but retained for future flexibility.

📝 Commit  
feat(auth+mail): password reset flow with JWT + migrate emails to Mandrill transactional
-------------------------
📓 Changelog — Chat Session Management: Auto-Naming, Rename, Delete  
📅 Date: 2025-07-14

✅ Added

🧠 Automatic session naming using Vertex AI  
- Integrated `TITLE_GEN_ASSISTANT_CONFIG` using `gemini-1.5-flash` to generate session titles.
- Added bilingual (ES/EN) `system_instruction` and prompt to contextualize user messages in legal chat.
- Title generation is triggered when a new session receives its first message.
- Context includes:
  - `msg` (user message)
  - Optional `file_data` from PDF or DOCX attachments
- Result is saved to MongoDB in `sessions.name`.

📝 Session renaming (manual)  
- New endpoint: `POST /assistant/renameSession/<session_id>`
  - JSON body:
    ```json
    {
      "new_name": "Nuevo título de sesión"
    }
    ```
  - Validates:
    - User ownership of session
    - `new_name` is not empty
  - Updates `name` field in MongoDB
  - Returns:
    - `200` on success
    - `404` if session not found
    - `400` if name is invalid

🗑️ Session deletion  
- New endpoint: `DELETE /assistant/deleteSession/<session_id>`
  - Deletes the session only if it belongs to the current user (`g.userId`)
  - Returns:
    - `200` on successful deletion
    - `404` if session not found or not owned

🧩 Controller updates  
- `controllers/assistantController.py`:
  - Added:
    - `renameSession(session_id, request)`
    - `deleteSession(session_id)`
    - Title model instantiation with `TITLE_GEN_ASSISTANT_CONFIG`
  - Refactored:
    - `chatSession(...)` to support title generation only when session is new (`len(history) == 0`)
    - Injection of file data into prompt context
- `routes/assistantBlueprint.py`:
  - Registered new routes:
    ```python
    @assistant_Router.post("/renameSession/<session_id>")
    @assistant_Router.delete("/deleteSession/<session_id>")
    ```

🧪 Environment configuration  
- Added `.env` variable references if needed for title model configuration.
- Requires valid Vertex AI service key at: `controllers/util/service_key.json`.

📝 Commit  
feat(chat): add auto-naming with Vertex, session rename and delete endpoints
----------------------
📓 Changelog — Contact Form Integration with Mailchimp  
📅 Date: 2025-07-03

✅ Added

📬 Mailchimp contact registration  
- Added `controllers/mailchimpController.py` with:
  - `MailchimpController` class to manage Mailchimp Marketing API interactions.
  - `add_contact(...)` method to create contacts in the default Mailchimp list.
  - `list_audiences(...)` helper method to fetch existing Mailchimp audiences and confirm list configuration.
- Uses official `mailchimp_marketing` client with:
  - `email_address`
  - `merge_fields`: `FNAME`, `LNAME`, optional `PHONE`
  - `status`: `"subscribed"`
  - Optional `notes`: stores the user's message

📨 Admin notification via email  
- Reused `email_utils.py` to add:
  - `notify_admin_new_contact(...)`: sends formatted HTML email to notify the admin of a new contact
- Admin email address comes from `.env` (`MAILCHIMP_ADMIN_NOTIFY_EMAIL`)  
- Email is sent using `MAIL_DEFAULT_SENDER` as the sender

🌐 Contact API route  
- Added `routes/contactBlueprint.py`, renamed its blueprint to `contact_Router`
- Defined route: `POST /contact/contact`
  - Accepts: `nombre`, `apellidos`, `email` (required), optional `telefono`, `mensaje`
  - Validates required fields before processing
  - On success: registers in Mailchimp and notifies the admin via email
  - Returns:
    - `400` if required fields are missing or Mailchimp responds with an error
    - `500` on internal exceptions (e.g. email config missing)

🧩 Router update  
- Registered the contact route in `routes/router.py`:
  ```python
  from routes.contactBlueprint import contact_Router
  router.register_blueprint(contact_Router, url_prefix="/contact")

🧪 Environment configuration

📝 Commit
feat(contact): integrate Mailchimp contact registration, list lookup, and admin notification via email
--------------------
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