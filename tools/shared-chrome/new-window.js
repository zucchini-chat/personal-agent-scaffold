async (page) => {
  const url = 'about:blank#' + Math.random().toString(36).slice(2, 8);
  const cdp = await page.context().browser().newBrowserCDPSession();
  const { targetId } = await cdp.send('Target.createTarget', { url, newWindow: true });
  for (let attempt = 0; attempt < 50; attempt++) {
    const pages = page.context().pages();
    for (let i = 0; i < pages.length; i++) {
      if (pages[i].url() !== url) continue;
      const s = await page.context().newCDPSession(pages[i]);
      const { targetInfo } = await s.send('Target.getTargetInfo');
      await s.detach();
      if (targetInfo.targetId === targetId) return { index: i, url };
    }
    await page.waitForTimeout(100);
  }
  throw new Error('new window not found: ' + url);
}
