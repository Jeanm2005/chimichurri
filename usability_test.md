# Usability Testing Feedback Report

---

## Intro

Two prototype features were tested in this round of usability testing:

1. Search radius drag feature
2. Friends chat feature

---

## Tasks

| Task | Result |
|------|--------|
| "Find a game and join it" | Completed easily by all testers |
| "Ask your friend if they'd like to join you for a game" | Completed easily by all testers |

---

## Notes

- After joining a game, testers naturally explored the search radius feature, which was expected behavior.
- Users expected a post-join prompt to invite friends to the same game they just joined — this transition felt like a missing step.
- The Friends tab houses the chat/messaging functionality, but users instinctively looked for it under a "Messages" section, which is the more common UX convention.
- The map displays joinable games, creating ambiguity about whether joining from the map and joining from the game list are the same action or different ones.
- Join button bugs were observed: the soccer join button was unresponsive, and the tennis game showed "1 spot left" but the count did not update after joining.
- Swapping the map and game-finding column positions would be preferable — map on the left and larger, list on the right and smaller.
- Search filters appear in more than one place, causing redundancy and confusion; one consistent location should be chosen.
- A drag handle for panels would improve layout flexibility.
- Profile access should be moved into the Settings section rather than having a dedicated top-level button.
- The profile page should be replaced with an activity page, with "Edit Profile" moved into Settings.
- The map should be removed from both the activity page and the profile page.

---

## Feedback

**How easy or hard was it to complete the tasks?**
Both tasks were straightforward and completed quickly across all testers. The interface was described as simple, intuitive, and clearly labeled. Finding and joining a game was easy to follow, and inviting a friend was equally simple given the labeled buttons and familiar messaging-like functionality.

**What confusions were there and why?**
- The Friends tab caused a moment of hesitation — users typically associate chat or messaging with a "Messages" section, not "Friends," so the location of that feature was not immediately obvious.
- The search radius map showing joinable games created confusion about whether it was a duplicate of the game list or a separate way to join. The relationship between the two entry points was unclear.
- One tester accidentally accepted a friend request with no way to undo it, which felt abrupt and error-prone due to the lack of any confirmation step.

**What could be improved?**
- Add a confirmation dialog with a cancel option when accepting friend requests to prevent accidental actions and provide clearer feedback.
- Clarify how the map and game list relate to each other, whether visually or through labeling.
- Consider renaming or restructuring the Friends tab so that its messaging functionality is easier to find.
- Add a prompt after joining a game to invite friends to that same game.

---

## Results

- Add a confirmation step (with cancel option) when accepting friend requests. A follow-up confirmation message upon acceptance would also improve feedback clarity.
- Fix join button functionality: the soccer join button was unresponsive, and the tennis spot count did not update after joining.
- Make the integration between the map and the game list clearer so users understand they are two views of the same action, not separate flows.
- Restructure the Friends tab or adjust labeling so that messaging functionality is discoverable for users expecting a traditional Messages section.
- Add a post-join flow that prompts users to invite friends to the game they just joined.
- Consolidate search filters to a single location to eliminate redundancy.
- Swap the map and list column layout, with the map on the left and larger, and the list on the right and smaller.
- Add panel drag handles for layout flexibility.
- Move profile access into Settings and replace the profile page with an activity page; remove the map from both the activity and profile pages.
