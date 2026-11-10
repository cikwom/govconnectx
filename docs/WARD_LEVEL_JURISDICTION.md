# Ward-level department jurisdiction

Department coverage now supports State-wide, LGA-wide, and ward-only scopes. Ward scopes require an active ward whose parent LGA matches the selected LGA and State. Existing scope rows migrate with a null ward code and preserve their previous State/LGA coverage.

The same backend match is used for staff report lists, report details and related staff actions, department performance metrics, manual assignment, and automatic category routing. A ward-only scope does not match reports without that ward. Citizen home geography is never used for routing; the incident location is the key. GPS review remains separate and cannot silently overwrite the citizen-selected incident area.

Ward/community directory records must come from documented authoritative INEC or state/local-government sources. Do not fabricate codes or boundaries. Bulk imports should retain source attribution and effective dates, and validate ward-to-LGA and community-to-ward parent relationships before committing.

Automated regression coverage checks ward parent validation, staff visibility within a ward, and ward-specific automatic routing. Manual browser validation with two wards in one LGA is still required before deployment.
