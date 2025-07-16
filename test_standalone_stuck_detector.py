# test_standalone_stuck_detector.py
# This script contains unit tests for the StandaloneStuckDetector.
# Each test case is designed to verify one of the specific "stuck" patterns,
# ensuring the core logic is preserved and understood.

import unittest
from standalone_stuck_detector import (
    State,
    StandaloneStuckDetector,
    CmdRunAction,
    CmdOutputObservation,
    ErrorObservation,
    MessageAction,
    AgentCondensationObservation,
    EventSource
)

class TestStandaloneStuckDetector(unittest.TestCase):

    def test_treasure_1_definition_of_insanity_loop(self):
        """Tests the classic 'doing the same thing and expecting different results' loop."""
        print("\nTesting Treasure 1: Definition of Insanity Loop...")
        action = CmdRunAction(command="ls -F")
        # Note: command_id is different, but _eq_no_pid should ignore it.
        obs1 = CmdOutputObservation(content="file.txt", command="ls -F", command_id=101)
        obs2 = CmdOutputObservation(content="file.txt", command="ls -F", command_id=102)
        obs3 = CmdOutputObservation(content="file.txt", command="ls -F", command_id=103)
        obs4 = CmdOutputObservation(content="file.txt", command="ls -F", command_id=104)
        
        history = [action, obs1, action, obs2, action, obs3, action, obs4]
        detector = StandaloneStuckDetector(State(history))
        self.assertTrue(detector.is_stuck(), "Should detect a simple action-observation loop")
        print("OK")

    def test_treasure_2_persistent_failure_loop(self):
        """Tests the loop where an action persistently results in an error."""
        print("Testing Treasure 2: Persistent Failure Loop...")
        action = CmdRunAction(command="cat non_existent_file")
        error_obs = ErrorObservation("File not found")
        
        history = [action, error_obs, action, error_obs, action, error_obs]
        detector = StandaloneStuckDetector(State(history))
        self.assertTrue(detector.is_stuck(), "Should detect a persistent action-error loop")
        print("OK")

    def test_treasure_3_agents_echo_chamber_loop(self):
        """Tests the agent getting stuck in a monologue, talking to itself."""
        print("Testing Treasure 3: Agent's Echo Chamber...")
        action1 = MessageAction(content="I should check the file.")
        action2 = MessageAction(content="I should check the file.")
        action3 = MessageAction(content="I should check the file.")

        history = [action1, action2, action3]
        detector = StandaloneStuckDetector(State(history))
        self.assertTrue(detector.is_stuck(), "Should detect a monologue loop")
        print("OK")

    def test_treasure_4_complex_rhythmic_loop(self):
        """Tests a more complex A-B-A-B rhythmic loop."""
        print("Testing Treasure 4: Complex Rhythmic Loop...")
        action_a = CmdRunAction(command="ls /path1")
        obs_a = CmdOutputObservation(content="file1.txt", command="ls /path1")
        action_b = CmdRunAction(command="ls /path2")
        obs_b = CmdOutputObservation(content="file2.txt", command="ls /path2")

        history = [
            action_a, obs_a, action_b, obs_b,
            action_a, obs_a, action_b, obs_b,
            action_a, obs_a, action_b, obs_b,
        ]
        detector = StandaloneStuckDetector(State(history))
        self.assertTrue(detector.is_stuck(), "Should detect an A-B-A-B rhythmic loop")
        print("OK")

    def test_treasure_5_context_trimming_death_spiral(self):
        """Tests the context window trimming failure loop."""
        print("Testing Treasure 5: Context Trimming Death Spiral...")
        history = [AgentCondensationObservation()] * 10
        detector = StandaloneStuckDetector(State(history))
        self.assertTrue(detector.is_stuck(), "Should detect a context condensation loop")
        print("OK")

    def test_treasure_6_dynamic_context_with_headless_mode(self):
        """Tests the crucial difference between headless and interactive modes."""
        print("Testing Treasure 6: Dynamic Context (Headed vs. Headless)...")
        action = CmdRunAction(command="ls")
        obs = CmdOutputObservation(content="file.txt", command="ls")
        
        # This history would be a loop, but a user message breaks it.
        history = [
            action, obs, action, obs, action, obs, # A loop of 3
            MessageAction("No, try something else.", source=EventSource.USER),
            action, obs # Not a loop after the user message
        ]
        
        # In interactive mode (headless=False), it should NOT be stuck.
        detector_interactive = StandaloneStuckDetector(State(history))
        self.assertFalse(detector_interactive.is_stuck(headless_mode=False), 
                         "Should NOT be stuck in interactive mode after a user message")
        print("OK - Interactive mode passed")

        # In headless mode, it SHOULD be stuck because it checks the whole history.
        detector_headless = StandaloneStuckDetector(State(history))
        self.assertTrue(detector_headless.is_stuck(headless_mode=True),
                        "Should BE stuck in headless mode as it checks the entire history")
        print("OK - Headless mode passed")

    def test_healthy_history_should_not_be_stuck(self):
        """Tests a normal, healthy progression of actions to prevent false positives."""
        print("Testing Healthy History...")
        history = [
            CmdRunAction("ls"),
            CmdOutputObservation(content="file.txt", command="ls"),
            CmdRunAction("cat file.txt"),
            CmdOutputObservation(content="hello", command="cat file.txt"),
            MessageAction("Task complete.")
        ]
        detector = StandaloneStuckDetector(State(history))
        self.assertFalse(detector.is_stuck(), "A healthy history should not be detected as stuck")
        print("OK")

if __name__ == '__main__':
    print("Running tests for StandaloneStuckDetector...")
    unittest.main()
