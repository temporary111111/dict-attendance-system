# Login at Public Attendance UI Design

## Goal

I-refresh ang login at public attendance pages para tumugma sa modern at formal na DICT admin workspace. Dapat compact, madaling sundan, responsive, accessible, at may maayos na dark mode nang hindi binabago ang kasalukuyang authentication at attendance behavior.

## Scope

- Admin login page (`index.html`)
- Public attendance page (`attendance.html`)
- Loading, error, form, consent confirmation, submitting, at success states
- Light at dark themes
- Desktop at mobile layouts

Hindi kasama ang backend, database, field requirements, consent wording, validation rules, signature behavior, o API contracts.

## Visual Direction

Gagamitin ang consistent DICT workspace style:

- Formal DICT blue bilang brand anchor, kasama ang neutral surfaces at restrained status colors.
- Compact typography at spacing para hindi overwhelming.
- Walang gradient, decorative orb, oversized marketing hero, o nested cards.
- Maximum 8px ang component border radius.
- Material Symbols ang gagamitin para sa familiar interface icons.

## Login Page

Sa desktop, mananatili ang dalawang malinaw na bahagi: DICT identity panel at actual login form. Ang branding panel ay magiging simple at official-looking, hindi marketing page. Ang form ang pangunahing action at makikita agad ang email, password, remember-device option, submit button, at backend connection status.

Ang desktop DICT identity panel ay gagamit ng enlarged `dict-header.png` bilang background image sa ilalim ng controlled dark-blue overlay. Mananatili ang white DICT logo card sa taas, habang ang overlay ang magpapanatiling readable ng title at supporting text. Hindi ito gagamitin sa mobile layout para manatiling compact ang sign-in workflow.

Sa mobile, mawawala ang malaking side panel. Lalabas ang compact DICT identity, theme toggle, at login form sa isang readable single-column layout. Walang horizontal overflow at hindi tatama ang controls sa viewport edges.

Ang password visibility control ay gagamit ng familiar visibility icon na may tooltip at accessible label. Hindi babaguhin ang login validation, session storage, o redirect behavior.

## Public Attendance Page

Ang page ay magiging document-style workflow sa constrained content width:

1. Compact header na may DICT logo, optional program logo, at public theme toggle.
2. Event identity at event details bago ang form.
3. Privacy notice na malinaw at visible bago personal data fields.
4. Full-width form sections para sa attendee information, PSGC address, signature, at consent.
5. Malinaw na final submit action at existing consent confirmation dialog.

Hindi gagawing multi-step form para maiwasan ang dagdag navigation at state complexity. Sa mobile, magiging isang column ang fields. Sa desktop, dalawang column lamang kapag natural na magkapareha ang fields.

Ang signature draw/upload control ay mananatiling segmented choice para malinaw na isang method lang ang kailangan. Ang hidden fields ay hindi mag-iiwan ng visual gap.

## Theme Isolation

- Login at admin workspace: `dict-attendance-admin-theme`
- Public attendance page: `dict-attendance-public-theme`

Parehong susunod sa operating-system theme sa unang visit. Kapag manual na pumili ang user, mase-save lamang ang preference sa `localStorage` ng kasalukuyang browser at origin. Hindi ito ise-save sa database.

Hindi maaapektuhan ng public preference ang admin/login preference kahit pareho silang gamitin sa isang browser.

## Page States

- **Loading:** compact spinner at direct status message.
- **Unavailable/error:** clear title, explanation, at stable centered layout.
- **Validation error:** inline field message, visible form-level feedback, at focus sa unang invalid control.
- **Submitting:** disabled controls at visible button loading state.
- **Success:** confirmation icon, attendee name, event name, at submitted timestamp.

Lahat ng states ay dapat readable sa light at dark themes.

## Accessibility at Responsiveness

- Keyboard-accessible controls at visible focus indicators.
- Icon-only buttons ay may `aria-label`, title, at stable 40x40px target.
- Minimum accessible contrast para sa normal text at action buttons.
- `prefers-reduced-motion` safeguards ay mananatili.
- Walang page-level horizontal overflow sa 390px mobile viewport.
- Walang text o controls na clipped sa supported desktop at mobile widths.

## Verification

- Static UI regression tests para sa separate theme keys, required theme controls, at responsive safeguards.
- Frontend smoke check at JavaScript syntax checks.
- Browser audit ng login at public attendance loading, form, consent dialog, error, at success states.
- Visual verification sa desktop/mobile at light/dark themes.
- Existing API calls, field visibility, validation, signature, at submission flow ay mananatiling functional.

## Acceptance Criteria

- Visually consistent ang login, attendance, at admin workspace.
- Independent ang admin at public theme preferences.
- Gumagana ang manual theme toggle at system-theme fallback.
- Compact at readable ang attendance form kahit maraming visible fields.
- Walang regression sa login o attendance behavior.
- Walang browser console error, clipped control, o page-level overflow sa audited states.
