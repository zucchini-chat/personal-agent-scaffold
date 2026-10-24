async (page) => {
  const quietMs = 1000, timeoutMs = 20000;
  const start = Date.now();
  await page.waitForLoadState('load', { timeout: timeoutMs });
  const networkIdle = await page.waitForLoadState('networkidle', { timeout: timeoutMs }).then(() => true, () => false);
  const domQuiet = await page.evaluate(({ quietMs, deadline }) => new Promise(resolve => {
    let timer;
    const done = ok => { observer.disconnect(); clearTimeout(timer); clearTimeout(cap); resolve(ok); };
    const observer = new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(() => done(true), quietMs); });
    observer.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
    timer = setTimeout(() => done(true), quietMs);
    const cap = setTimeout(() => done(false), Math.max(deadline - Date.now(), 0));
  }), { quietMs, deadline: start + timeoutMs });
  const busy = await page.locator('[aria-busy="true"], [role="progressbar"], .spinner, .loading, .skeleton').filter({ visible: true }).count();
  return { ready: networkIdle && domQuiet && busy === 0, networkIdle, domQuiet, busyIndicators: busy, ms: Date.now() - start };
}
