(async () => {
  const possibleButtons = Array.from(document.querySelectorAll('button, [role="button"]'));

  const addFriendButtons = possibleButtons.filter(btn => {
      const text = btn.textContent || "";
      const ariaLabel = btn.getAttribute('aria-label') || "";
      return text.includes('Add Friend') || ariaLabel.includes('Add Friend');
  });

  console.log(`Found ${addFriendButtons.length} 'Add Friend' buttons.`);

  const minDelay = 4000;
  const maxDelay = 9000;

  for(let i = 0; i < addFriendButtons.length; i++) {
      try {
          addFriendButtons[i].click();

          const randomDelay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;

          console.log(`Clicked button #${i + 1}/${addFriendButtons.length}. Waiting ${(randomDelay / 1000).toFixed(1)}s...`);

          await new Promise(resolve => setTimeout(resolve, randomDelay));
      } catch(error) {
          console.error(`Failed to click button #${i + 1}`, error);
      }
  }
  console.log("Finished clicking all found buttons!");
})();
