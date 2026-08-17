from .user_schema import Intent, UserSchema
from datetime import date, datetime, timedelta

entries = [
    {
        "id": "entry_001",
        "user": UserSchema(
            name="James Smith",
            email="james.smith1@example.com",
            phone="+1-555-0001",
            customer_id="CUST001",
            known_information="Purchased a Samsung Galaxy S24 Ultra (barcode: 8806095690001) two weeks ago from the New York Main Branch. The phone has been randomly restarting and the screen flickers occasionally. Prefers diagnostic using Samsung Official Equipment.",
            unknown_information="Root cause of device malfunction, warranty coverage status, repair cost estimate, parts availability",
            high_level_intent=Intent.SERVICE_AND_REPAIR,
            goal="Diagnose intermittent restart and screen issues, determine warranty coverage, obtain repair estimate.",
        ),
        "task_instructions": """The customer is ONLY asking for three things:
        1. A diagnostic scan to identify the issue
        2. Warranty coverage status
        3. A repair estimate if needed

        Only use check_warranty_status, run_diagnostic_scan, search_database, and generate_repair_estimate tools to fulfill the request.

        Follow these steps:
        STEP 1: Check warranty status
        - Call check_warranty_status with:
            * barcode: Ask the customer for information or use known information
            * customer_id: The customer_id from customer's information
        - Note the warranty expiry date to determine if coverage is available
        - Confirm if repairs are covered under warranty or require payment

        STEP 2: Run diagnostic scan
        - Use run_diagnostic_scan with:
            * barcode: Same barcode as the previous tool call
            * customer_id: Same customer_id
            * symptoms_description: Summarize the issues the customer described (random restarts, screen flickering)
        - The scan will return diagnostic codes and recommendations about which parts need replacement
        - Note the recommended parts/components that need to be replaced

        STEP 3: Search for parts in the database
        - Based on the diagnostic scan recommendations, search for the required parts in the inventory
        - Use search_database on the 'inventory' database to find parts matching the diagnostic results
        - Search for parts related to the issue (e.g., if diagnostic mentions "display module" or "battery", search for those in part_name or description)
        - From the search results, note:
            * barcode: The part identifier
            * price: The price of the part
            * installation_time: The labor hours needed for repair
        - You MUST use the actual barcode from the database, not made-up identifiers

        STEP 4: Schedule service appointment
        - Use schedule_service_appointment with:
            * customer_id: Same as above
            * product_barcode: The device barcode
            * service_type: "diagnostics" for initial scan or "repair" for confirmed repair
            * preferred_datetime: Ask customer or suggest tomorrow
            * branch_code: The branch from customer's known information
            * notes: Include diagnostic findings and warranty status

        STEP 5: Provide final response and STOP the conversation
        CRITICAL:
        - Use ONLY information directly from the tool outputs. Do NOT add details that weren't in the tool results.
        - Use the EXACT dollar amounts returned by tools. Do NOT recalculate.
        - Report the EXACT diagnostic findings from the diagnostic scan tool. Do NOT make up additional details.

        Your response should include ONLY:
        - Root cause: Report what the diagnostic scan tool actually identified
        - The specific part that needs replacement (from database search)
        - Warranty status based on warranty tool output
        - Complete cost breakdown using EXACT values from tools
        - Appointment confirmation details

        STOP immediately after providing the diagnosis, warranty status, estimate, and appointment confirmation.""",
        "initial_user_query": "Hi, I bought a Samsung Galaxy S24 Ultra about two weeks ago and it's been acting up. The phone keeps restarting randomly and the screen flickers sometimes. I need a diagnostic scan and want to know if this is covered by warranty and get a repair estimate.",
        "target": {
            "tools": [
                {
                    "name": "check_warranty_status",
                    "parameters": {
                        "barcode": "8806095690001",
                        "customer_id": "CUST001"
                    }
                },
                {
                    "name": "run_diagnostic_scan",
                    "parameters": {
                        "barcode": "8806095690001",
                        "customer_id": "CUST001",
                        "symptoms_description": "Random restarts and screen flickering"
                    }
                },
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "inventory"
                    }
                },
                {
                    "name": "schedule_service_appointment",
                    "parameters": {
                        "customer_id": "CUST001",
                        "product_barcode": "8806095690001",
                        "service_type": "diagnostics",
                        "preferred_datetime": "*",
                        "branch_code": "BRN_NY_MAIN",
                        "notes": "*"
                    }
                }
            ],
            "text": "Diagnostic scan completed on your Samsung Galaxy S24 Ultra. The scan identified display module issues and battery connection faults. Based on the diagnostic results, the display module needs to be replaced.\n\n**Warranty Status:** The device warranty is active and covers the repair.\n\n**Repair Estimate:**\n- Parts: Cost for display module replacement\n- Labor: Cost for diagnostic and repair work\n- **Total: Combined estimate covering parts and labor under warranty**\n\nService appointment scheduled at New York Main Branch."
        }
    },
    {
        "id": "entry_002",
        "user": UserSchema(
            name="Mary Johnson",
            email="mary.johnson2@example.com",
            phone="+1-555-0002",
            customer_id="CUST002",
            known_information="Wants to buy an Apple iPhone 15 Pro Max (256GB). Located near the Los Angeles City Branch. Has a budget of around $1200-1500. Credit score of 720 and annual income of $75,000.",
            unknown_information="Current price, availability at the LA branch, exact barcode for 256GB model",
            high_level_intent=Intent.PURCHASE,
            goal="Find and purchase iPhone 15 Pro Max 256GB at the best available price within budget.",
        ),
        "task_instructions": """The customer, Mary Johnson, wants to purchase an Apple iPhone 15 Pro Max with 256GB storage at the Los Angeles branch.

STEP 1: Use **search_database** to find the customer's information
   - Search the customers database using email mary.johnson2@example.com
   - Confirm customer_id is CUST002
   - Note customer preferences and purchase history

STEP 2: Use **search_database** to find available iPhone 15 Pro Max (256GB) in inventory
   - Search criteria: brand='Apple', model contains 'iPhone 15 Pro Max', storage='256GB', branch_code='BRN_CA_LA'
   - Note the barcode, price, and stock quantity from results
   - Verify the price is within customer's budget ($1200-1500)

STEP 3: Use **check_product_availability** to verify stock at LA branch
   - barcode: From STEP 2
   - branch_code: BRN_CA_LA
   - Confirm actual availability and any special offers

STEP 4: Use **generate_purchase_invoice** to complete the purchase
   - barcode: From STEP 2
   - customer_id: CUST002 (from STEP 1)
   - quantity: 1
   - This will return an invoice_number and total amount

STEP 5: In your final response, confirm:
   - Product found (iPhone 15 Pro Max 256GB with barcode and price)
   - Availability confirmed at Los Angeles City Branch
   - Purchase invoice generated with invoice number
   - Total amount paid
   - Customer can pick up at branch or delivery options

DO NOT add extra fields to any parameters. Only use the fields explicitly specified above.""",
        "initial_user_query": "Hello! I'm looking to buy an iPhone 15 Pro Max with 256GB storage. Can you check if it's available at the Los Angeles store and what the price is? If it's in stock and within my budget, I'd like to purchase it today.",
        "target": {
            "tools": [
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "customers"
                    }
                },
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "inventory"
                    }
                },
                {
                    "name": "check_product_availability",
                    "parameters": {
                        "barcode": "0194253001195",
                        "branch_code": "BRN_CA_LA"
                    }
                },
                {
                    "name": "generate_purchase_invoice",
                    "parameters": {
                        "barcode": "0194253001195",
                        "customer_id": "CUST002",
                        "quantity": 1
                    }
                }
            ],
            "text": [
                "Found iPhone 15 Pro Max 256GB at Los Angeles City Branch, priced at $1,299. Stock confirmed available. Purchase invoice generated with invoice number. You can pick up your device at the store or arrange delivery."
            ]
        }
    },
    {
        "id": "entry_003",
        "user": UserSchema(
            name="Robert Williams",
            email="robert.williams3@example.com",
            phone="+1-555-0003",
            customer_id="CUST003",
            known_information="Purchased Sony WH-1000XM5 headphones (barcode: 4548736132818) last month from Chicago Downtown Branch. The noise cancellation stopped working properly after a week. Has original receipt and packaging.",
            unknown_information="Exchange policy details, availability of replacement unit at Chicago branch, whether this requires a restocking fee",
            high_level_intent=Intent.EXCHANGE,
            goal="Exchange the defective headphones for a new pair of the same model with no additional cost.",
        ),
        "task_instructions": """The customer, Robert Williams, wants to exchange defective Sony WH-1000XM5 headphones purchased last month.

STEP 1: Use **search_database** to find the customer_id for Robert Williams
   - Search the customers database using email robert.williams3@example.com
   - Verify customer_id CUST003
   - Look for purchase history to confirm the original transaction

STEP 2: Use **search_database** to find the original product details
   - Search inventory database for Sony WH-1000XM5 using barcode 4548736132818
   - Confirm product exists and note the specifications
   - Check warranty coverage period for this product

STEP 3: Use **check_product_availability** to verify replacement stock
   - barcode: 4548736132818 (same model for exchange)
   - branch_code: BRN_IL_CHI (Chicago Downtown Branch)
   - Confirm replacement unit is available in stock
   - Note quantity available and any wait time if out of stock

STEP 4: Use **process_exchange_request** to complete the exchange
   - original_barcode: 4548736132818
   - new_barcode: 4548736132818 (same product)
   - customer_id: CUST003
   - reason: "defective" (IMPORTANT: Use exactly this value - defective products have no restocking fee)
   - branch_code: BRN_IL_CHI
   - This will return an exchange_authorization_number

STEP 5: In your final response, confirm:
   - Exchange request approved
   - Product availability confirmed at Chicago Downtown Branch
   - Exchange authorization number provided
   - NO restocking fee (defective exchange policy)
   - Instructions for bringing defective unit to store
   - Customer will receive new unit immediately upon return

DO NOT add extra fields to any parameters. Only use the fields explicitly specified above.""",
        "initial_user_query": "I bought Sony WH-1000XM5 headphones about a month ago from your Chicago store, but the noise cancellation stopped working after just a week of use. This is clearly defective. I'd like to exchange them for a new pair - I have the receipt and original packaging.",
        "target": {
            "tools": [
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "customers"
                    }
                },
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "inventory"
                    }
                },
                {
                    "name": "check_product_availability",
                    "parameters": {
                        "barcode": "4548736132818",
                        "branch_code": "BRN_IL_CHI"
                    }
                },
                {
                    "name": "process_exchange_request",
                    "parameters": {
                        "original_barcode": "4548736132818",
                        "new_barcode": "4548736132818",
                        "customer_id": "CUST003",
                        "reason": "defective",
                        "branch_code": "BRN_IL_CHI"
                    }
                }
            ],
            "text": [
                "Your exchange request has been approved with authorization number provided. Replacement Sony WH-1000XM5 headphones confirmed in stock at Chicago Downtown Branch. Since this is a defective product exchange, there is NO restocking fee. Please bring your defective headphones with the original receipt to the Chicago Downtown Branch to receive your replacement unit immediately."
            ]
        }
    },
    {
        "id": "entry_004",
        "user": UserSchema(
            name="Patricia Brown",
            email="patricia.brown4@example.com",
            phone="+1-555-0004",
            customer_id="CUST004",
            known_information="Looking for a laptop for her daughter who is starting college in the fall. Needs something reliable for schoolwork, Microsoft Office, and light video editing. Prefers good battery life (8+ hours). Budget is around $1000-1300. Prefers Apple or Dell brands. Interested in comparing options across all branches to find the best deal.",
            unknown_information="Available laptop models in budget range, specific battery life specifications, which branches have stock, processor speeds, RAM configurations",
            high_level_intent=Intent.PRODUCT_INQUIRY,
            goal="Find and compare available laptops within budget that meet college requirements, then select the best option based on features and price.",
        ),
        "task_instructions": """The customer, Patricia Brown, is looking for a laptop for her daughter's college needs. She wants to compare options from Apple and Dell within her $1000-1300 budget.

STEP 1: Use **search_database** to find the customer's profile
   - Search customers database using email patricia.brown4@example.com
   - Confirm customer_id CUST004
   - Note any previous purchases or preferences

STEP 2: Use **search_database** to find available laptops from Apple and Dell
   - Search inventory database for laptops
   - Filter by:
     * Brand: Apple OR Dell
     * Category: Laptops
     * Price range: $1000-1300
     * Available across all branches
   - From results, note for each laptop:
     * barcode
     * brand and model
     * price
     * specifications (processor, RAM, storage)
     * battery_life
     * branch_code and stock quantity

STEP 3: Present comparison of options
   - List at least 2-3 laptop options that meet requirements
   - Highlight key features for college use:
     * Battery life (8+ hours preferred)
     * Processor speed and RAM for Office and video editing
     * Storage capacity
     * Portability (weight and screen size)
   - Show which branches have each model in stock
   - Compare prices and note best value

STEP 4: If customer selects a specific laptop
   - Use **check_product_availability** to verify current stock
     * barcode: The selected laptop's barcode
     * branch_code: Customer's preferred branch or best availability
   - Confirm exact quantity available and expected delivery/pickup time

STEP 5 (Optional): If customer wants to purchase
   - Use **generate_purchase_invoice** to complete the sale
     * barcode: Selected laptop barcode
     * customer_id: CUST004
     * quantity: 1
   - Provide invoice details and pickup/delivery instructions

STEP 6: Provide final response
   - Summarize the laptop options presented
   - Highlight the best recommendation based on requirements
   - If purchase was made, confirm invoice and next steps

DO NOT add extra fields to any parameters. Only use the fields explicitly specified above.""",
        "initial_user_query": "Hi there! My daughter is starting college next semester and I want to get her a good laptop. She'll need it for schoolwork, Microsoft Office, and some light video editing. Battery life is important - at least 8 hours would be great. My budget is around $1000 to $1300. I prefer Apple or Dell if possible. Can you show me what options you have across all your stores and help me find the best one?",
        "target": {
            "tools": [
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "customers"
                    }
                },
                {
                    "name": "search_database",
                    "parameters": {
                        "query": "*",
                        "database_name": "inventory"
                    }
                }
            ],
            "text": [
                "Based on your requirements for college use, here are laptop options from Apple and Dell within your $1000-1300 budget:\n\n1. Dell XPS 13 - $1,249 (Available at Chicago, NY branches) - Intel i7, 16GB RAM, 512GB SSD, 12-hour battery life - Excellent for Office and light video editing\n\n2. MacBook Air M2 - $1,299 (Available at LA, Chicago branches) - Apple M2 chip, 8GB RAM, 256GB SSD, 15-hour battery life - Great battery life and performance for college tasks\n\n3. Dell Inspiron 15 - $1,099 (Available at all branches) - Intel i5, 12GB RAM, 512GB SSD, 10-hour battery life - Best value option\n\nBest recommendation for your daughter's needs: MacBook Air M2 for superior battery life and performance, or Dell XPS 13 for more RAM and storage at a lower price point."
            ]
        }
    },
]