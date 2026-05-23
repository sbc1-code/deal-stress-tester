"""
Independent math verification for BRRRR Stress Test Calculator.
Run: python3 test_math.py
All tests must pass before deploying changes to calculator logic.
"""

def mortgage_payment(principal, annual_rate, term_years):
    if principal <= 0: return 0
    if annual_rate <= 0: return principal / (term_years * 12)
    r = annual_rate / 100 / 12
    n = term_years * 12
    return principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

def remaining_balance(principal, annual_rate, term_years, months_paid):
    if principal <= 0: return 0
    if annual_rate <= 0:
        mp = principal / (term_years * 12)
        return max(0, principal - mp * months_paid)
    r = annual_rate / 100 / 12
    n = term_years * 12
    if months_paid >= n: return 0
    return principal * ((1 + r)**n - (1 + r)**months_paid) / ((1 + r)**n - 1)

def calc_deal(p):
    purchase = p['purchase']; down_pct = p['down_pct']; rate = p['rate']
    term = p['term']; rent = p['rent']; vacancy = p['vacancy']
    expenses = p['expenses']; capex_pct = p['capex_pct']
    close_buy_pct = p['close_buy_pct']; close_sell_pct = p['close_sell_pct']
    hold = p['hold']; appreciation = p['appreciation']; partners = p['partners']
    rehab = p.get('rehab', 0); arv = p.get('arv', purchase)
    refi_timing = p.get('refi_timing', 6); refi_rate = p.get('refi_rate', rate)
    refi_ltv = p.get('refi_ltv', 75); refi_closing_pct = p.get('refi_closing_pct', 2)

    down = purchase * (down_pct / 100)
    loan = purchase - down
    close_buy = purchase * (close_buy_pct / 100)
    total_invested = down + close_buy + rehab
    monthly_mtg = mortgage_payment(loan, rate, term)
    eff_rent = rent * (1 - vacancy / 100)
    capex_mo = rent * (capex_pct / 100)
    noi = eff_rent - expenses - capex_mo
    monthly_cf = noi - monthly_mtg
    annual_cf = monthly_cf * 12
    coc = (annual_cf / total_invested * 100) if total_invested > 0 else 0

    app_base = arv if (rehab > 0 and arv > purchase) else purchase
    sale = app_base * (1 + appreciation / 100)**hold
    close_sell = sale * (close_sell_pct / 100)
    months_paid = min(hold * 12, term * 12)
    balance = remaining_balance(loan, rate, term, months_paid)
    net_sale = sale - close_sell - balance
    total_cf_hold = annual_cf * hold
    total_profit = net_sale + total_cf_hold - total_invested
    per_partner = total_profit / partners

    total_return = total_profit / total_invested if total_invested > 0 else 0
    if total_invested > 0 and hold > 0 and total_return > -1:
        ann_roi = ((1 + total_return)**(1/hold) - 1) * 100
    else:
        ann_roi = -100

    hours = 5 * 12 * hold
    hourly = per_partner / hours if hours > 0 else 0

    refi_loan = arv * (refi_ltv / 100)
    orig_bal_refi = remaining_balance(loan, rate, term, refi_timing)
    refi_close = refi_loan * (refi_closing_pct / 100)
    cash_out = refi_loan - orig_bal_refi - refi_close
    net_cash_left = max(0, total_invested - max(0, cash_out))
    refi_mtg = mortgage_payment(refi_loan, refi_rate, term)
    post_refi_cf = noi - refi_mtg
    post_refi_annual = post_refi_cf * 12
    post_refi_coc = (post_refi_annual / net_cash_left * 100) if net_cash_left > 0 else (float('inf') if post_refi_annual > 0 else 0)

    post_refi_hold_mo = max(0, hold * 12 - refi_timing)
    refi_bal_sale = remaining_balance(refi_loan, refi_rate, term, post_refi_hold_mo)
    post_refi_net_sale = sale - close_sell - refi_bal_sale
    post_refi_total_cf = post_refi_annual * (post_refi_hold_mo / 12)
    pre_refi_cf = monthly_cf * refi_timing
    post_refi_profit = post_refi_net_sale + post_refi_total_cf + pre_refi_cf - total_invested

    return {
        'monthly_mtg': monthly_mtg, 'monthly_cf': monthly_cf, 'coc': coc,
        'sale': sale, 'net_sale': net_sale, 'total_profit': total_profit,
        'ann_roi': ann_roi, 'hourly': hourly, 'app_base': app_base,
        'cash_out': cash_out, 'net_cash_left': net_cash_left,
        'refi_mtg': refi_mtg, 'post_refi_cf': post_refi_cf,
        'post_refi_coc': post_refi_coc, 'post_refi_net_sale': post_refi_net_sale,
        'post_refi_profit': post_refi_profit
    }

def assert_close(name, actual, expected, tol=1):
    threshold = max(tol, abs(expected) * 0.001)
    if abs(actual - expected) > threshold:
        raise AssertionError(f"FAIL: {name} = {actual:.2f}, expected {expected}")

# === TESTS ===

def test_default_no_brrrr():
    r = calc_deal({'purchase':300000,'down_pct':25,'rate':7,'term':30,'rent':2400,'vacancy':8,
                   'expenses':600,'capex_pct':5,'close_buy_pct':3,'close_sell_pct':8,
                   'hold':5,'appreciation':3,'partners':1,'rehab':0,'arv':300000})
    assert_close('mortgage', r['monthly_mtg'], 1496.93)
    assert_close('cash_flow', r['monthly_cf'], -8.93)
    assert_close('coc', r['coc'], -0.1, tol=0.2)
    assert_close('sale', r['sale'], 347782, tol=5)
    assert_close('ann_roi', r['ann_roi'], 5.1, tol=0.2)
    assert r['app_base'] == 300000, "App base should be purchase price when no rehab"

def test_brrrr_uses_arv():
    r = calc_deal({'purchase':300000,'down_pct':25,'rate':7,'term':30,'rent':2400,'vacancy':8,
                   'expenses':600,'capex_pct':5,'close_buy_pct':3,'close_sell_pct':8,
                   'hold':5,'appreciation':3,'partners':1,'rehab':50000,'arv':400000,
                   'refi_timing':6,'refi_rate':7,'refi_ltv':75,'refi_closing_pct':2})
    assert r['app_base'] == 400000, "App base should be ARV when BRRRR active"
    assert_close('sale', r['sale'], 463710, tol=5)
    assert r['post_refi_net_sale'] < r['net_sale'], "Post-refi sale proceeds should be lower (bigger loan)"

def test_real_4plex():
    r = calc_deal({'purchase':130000,'down_pct':25,'rate':7,'term':30,'rent':2400,'vacancy':8,
                   'expenses':600,'capex_pct':5,'close_buy_pct':3,'close_sell_pct':8,
                   'hold':5,'appreciation':3,'partners':3,'rehab':108000,'arv':280000,
                   'refi_timing':6,'refi_rate':7,'refi_ltv':75,'refi_closing_pct':2})
    assert r['app_base'] == 280000
    assert r['monthly_cf'] > 0, "Pre-refi cash flow should be positive on a $130K buy"
    assert r['refi_mtg'] > r['monthly_mtg'], "Refi mortgage should be higher (bigger loan)"

def test_zero_rate():
    r = calc_deal({'purchase':200000,'down_pct':20,'rate':0,'term':30,'rent':1500,'vacancy':5,
                   'expenses':400,'capex_pct':5,'close_buy_pct':3,'close_sell_pct':8,
                   'hold':10,'appreciation':2,'partners':1,'rehab':0,'arv':200000})
    assert_close('mortgage', r['monthly_mtg'], 444.44, tol=1)
    assert r['monthly_cf'] > 0

def test_cash_buy():
    r = calc_deal({'purchase':150000,'down_pct':100,'rate':7,'term':30,'rent':1200,'vacancy':10,
                   'expenses':300,'capex_pct':5,'close_buy_pct':3,'close_sell_pct':8,
                   'hold':3,'appreciation':0,'partners':2,'rehab':0,'arv':150000})
    assert r['monthly_mtg'] == 0, "No mortgage on cash buy"
    assert r['monthly_cf'] > 0, "Cash buy should have positive cash flow"

def test_declining_market():
    r = calc_deal({'purchase':250000,'down_pct':25,'rate':8,'term':30,'rent':2000,'vacancy':12,
                   'expenses':500,'capex_pct':5,'close_buy_pct':3,'close_sell_pct':8,
                   'hold':5,'appreciation':-3,'partners':1,'rehab':0,'arv':250000})
    assert r['sale'] < 250000, "Sale should be below purchase in declining market"
    assert r['total_profit'] < 0, "Should lose money in declining market with negative CF"

# === Verdict interpretation (port of JS interpret*() in index.html) ===
# Keep these in lock-step with the JS thresholds. Boundary tests below.

INFINITY = float('inf')

def interpret_cf(cf):
    if cf >= 200: return 'good'
    if cf >= 50: return 'warn'
    if cf >= 0: return 'warn'
    return 'bad'

def interpret_coc(coc):
    if coc == INFINITY: return 'good'
    if coc >= 12: return 'good'
    if coc >= 8: return 'good'
    if coc >= 5: return 'warn'
    if coc >= 0: return 'warn'
    return 'bad'

def interpret_mortgage(rent, mortgage):
    if mortgage == 0: return 'good'
    if rent == 0: return None
    ratio = (mortgage / rent) * 100
    if ratio < 50: return 'good'
    if ratio < 80: return 'warn'
    return 'bad'

def interpret_roi(roi):
    if roi >= 15: return 'good'
    if roi >= 8: return 'good'
    if roi >= 4: return 'warn'
    if roi >= 0: return 'warn'
    return 'bad'

def interpret_exit_profit(profit, invested):
    if profit < 0: return 'bad'
    if invested <= 0: return None
    multiple = profit / invested
    if multiple >= 1: return 'good'
    if multiple >= 0.5: return 'good'
    if multiple >= 0.1: return 'warn'
    return 'warn'

def interpret_hourly(hr):
    if hr < 0: return 'bad'
    if hr >= 50: return 'good'
    if hr >= 25: return 'warn'
    if hr >= 10: return 'warn'
    return 'bad'

def interpret_net_sale(net, invested):
    if net < 0: return 'bad'
    if invested > 0 and net < invested: return 'warn'
    return None

# === Verdict boundary tests ===

def test_verdict_cf_boundaries():
    assert interpret_cf(500) == 'good'
    assert interpret_cf(200) == 'good'       # exactly at good cutoff
    assert interpret_cf(199.99) == 'warn'    # just below
    assert interpret_cf(50) == 'warn'
    assert interpret_cf(0) == 'warn'         # breakeven still warn
    assert interpret_cf(-0.01) == 'bad'
    assert interpret_cf(-1000) == 'bad'

def test_verdict_coc_boundaries():
    assert interpret_coc(INFINITY) == 'good'
    assert interpret_coc(20) == 'good'
    assert interpret_coc(12) == 'good'
    assert interpret_coc(11.99) == 'good'    # still good above 8
    assert interpret_coc(8) == 'good'
    assert interpret_coc(7.99) == 'warn'
    assert interpret_coc(5) == 'warn'
    assert interpret_coc(0) == 'warn'
    assert interpret_coc(-0.01) == 'bad'
    assert interpret_coc(-50) == 'bad'

def test_verdict_mortgage_boundaries():
    assert interpret_mortgage(2000, 0) == 'good'        # cash buy
    assert interpret_mortgage(0, 1000) is None          # no rent edge case
    assert interpret_mortgage(2000, 999) == 'good'      # 49.95% ratio
    assert interpret_mortgage(2000, 1000) == 'warn'     # exactly 50%
    assert interpret_mortgage(2000, 1599) == 'warn'     # 79.95%
    assert interpret_mortgage(2000, 1600) == 'bad'      # exactly 80%
    assert interpret_mortgage(2000, 3000) == 'bad'      # 150%

def test_verdict_roi_boundaries():
    assert interpret_roi(20) == 'good'
    assert interpret_roi(15) == 'good'
    assert interpret_roi(8) == 'good'
    assert interpret_roi(7.99) == 'warn'
    assert interpret_roi(4) == 'warn'
    assert interpret_roi(0) == 'warn'
    assert interpret_roi(-0.01) == 'bad'

def test_verdict_exit_profit_boundaries():
    assert interpret_exit_profit(-1, 100000) == 'bad'
    assert interpret_exit_profit(0, 0) is None          # zero invested edge
    assert interpret_exit_profit(100000, 100000) == 'good'   # 1.0 multiple
    assert interpret_exit_profit(50000, 100000) == 'good'    # 0.5 multiple
    assert interpret_exit_profit(49999, 100000) == 'warn'    # just below 0.5
    assert interpret_exit_profit(10000, 100000) == 'warn'    # 0.1 multiple
    assert interpret_exit_profit(5000, 100000) == 'warn'     # below 0.1

def test_verdict_hourly_boundaries():
    assert interpret_hourly(100) == 'good'
    assert interpret_hourly(50) == 'good'
    assert interpret_hourly(49.99) == 'warn'
    assert interpret_hourly(25) == 'warn'
    assert interpret_hourly(10) == 'warn'
    assert interpret_hourly(9.99) == 'bad'
    assert interpret_hourly(0) == 'bad'
    assert interpret_hourly(-1) == 'bad'

def test_verdict_net_sale_boundaries():
    assert interpret_net_sale(-1, 100000) == 'bad'
    assert interpret_net_sale(0, 100000) == 'warn'      # zero proceeds, lost the invested
    assert interpret_net_sale(50000, 100000) == 'warn'  # exit with less than put in
    assert interpret_net_sale(100000, 100000) is None   # break even -> no opinion
    assert interpret_net_sale(200000, 100000) is None   # positive -> profit interp covers it
    assert interpret_net_sale(50000, 0) is None         # zero invested edge

def test_verdict_real_4plex_deal_voice():
    # Sebastian's real 4plex: bought $130K, rehab $108K, refi $280K, sold $400K,
    # netted ~$15K over 4.5 yrs, effective hourly < $6
    # Make sure the verdicts read the way the README story does.
    assert interpret_hourly(6) == 'bad'   # "sub-minimum wage" — matches story
    assert interpret_cf(-9) == 'bad'      # default-deal cash flow is -$9, should be bad
    assert interpret_exit_profit(15000, 84000) == 'warn'  # ~0.18 multiple
    assert interpret_net_sale(-3377, 84000) == 'bad'      # negative cash-out per current default

if __name__ == '__main__':
    tests = [test_default_no_brrrr, test_brrrr_uses_arv, test_real_4plex,
             test_zero_rate, test_cash_buy, test_declining_market,
             test_verdict_cf_boundaries, test_verdict_coc_boundaries,
             test_verdict_mortgage_boundaries, test_verdict_roi_boundaries,
             test_verdict_exit_profit_boundaries, test_verdict_hourly_boundaries,
             test_verdict_net_sale_boundaries, test_verdict_real_4plex_deal_voice]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} - {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    exit(0 if passed == len(tests) else 1)
