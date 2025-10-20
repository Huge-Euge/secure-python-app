# Requirements

## Functional

Users should be able to manage their account including:

- registering an account
- logging in
- logging out
- reseting their password - Maybe? this one seems outside of what the assignment is about

Once logged in users should be able to manage their notes:

- view a list of notes
- view a single note
- create a new note
- edit a note
- delete a note

Data must persist in between sessions

## Non-functional

Users shouldn't be able to access each others' notes
Users' data integrity should be maintained - notes and accounts
Users' data shouldn't be leaked while in transit - use HTTPS
Passwords should be stored securely, hashed and salted

# Threat Assessment

# Implementation Notes

# Testing and Review Notes

# Assumptions

We're not being graded on an attractive web site, UX/UI aren't something to focus on

# TODO

1. secure session tokens / auth with JWT
2. logout functionality
3. Notes page with editing / deleting
4. Tests for the endpoints

## Describe Security Measures for

1.
2.
3.
4.
5. Session fixation
6. Cross-site scripting
7. Replay attacks
8. SQL injection
9. Replay attacks
10. HTTPS
11. Session Timeout
12. DB backup
