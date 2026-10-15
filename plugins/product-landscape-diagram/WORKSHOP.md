# Product landscape diagram: workshop instructions

One person per group runs this on their laptop, shared on the group's screen.
Set it up before the session starts.

## Before the session (5 minutes)

1. Install Claude Code and sign in, if you have not already:
   https://code.claude.com

2. Open a terminal, make an empty folder for the session and start Claude Code in it:

   ```
   mkdir ~/product-workshop && cd ~/product-workshop
   claude
   ```

3. Inside Claude Code, add the marketplace and install the plugin:

   ```
   /plugin marketplace add dhis2-chap/claude-plugins
   /plugin install product-landscape-diagram@dhis2-chap
   ```

   If you added the marketplace earlier, refresh it first with
   `/plugin marketplace update dhis2-chap`.

4. Optional: if you have the `chap-infobase` repo cloned, or GitHub access to
   the `dhis2-chap` organisation so it can be cloned for you, the facilitator
   can use it to ask better questions. It is not required.

## During the session

1. Type `/product-landscape-diagram` and press enter.

2. The facilitator first asks whether to use the chap-infobase (pick "No / skip"
   if unsure), then runs three phases:

   - **Inventory:** the group lists all the tools and products it can think of,
     both the ones we build and external ones we depend on. Type them in one
     message; a rough list is fine. Then sort them with the clickable questions.
   - **One product at a time:** for each product, describe what it does and what
     it talks to, then confirm status and connections with clickable questions.
     The diagram is published as a link after the first connections are in.
     Open it in a browser on the shared screen. It updates by itself; drag to
     pan, scroll to zoom, press F to fit.
   - **Propose and iterate:** the facilitator proposes a cleaned-up diagram and
     asks what to change until the group is happy. Then it lists the open
     questions to bring to the plenary.

3. Clickable questions always have an "Other" option where you can type a
   free-text answer instead. Use it whenever the options do not fit.

4. The scope is fixed: **from getting data into DHIS2 to enabling decisions.**
   Naming of products is out of scope.

## Tips

- One person types; everyone talks. Paste in fragments of the discussion rather
  than polishing the text.
- Disagreements are recorded as open questions, not settled. Do not spend time
  arguing them out.
- If the facilitator asks about something you do not know, say so. It will move
  on.

## Afterwards

The files are in `product-workshop/product-landscape/`: `diagram.mmd` is the
Mermaid source (paste it into https://mermaid.live or a GitHub markdown file),
`register.md` has the table of products, open questions and assumptions.
