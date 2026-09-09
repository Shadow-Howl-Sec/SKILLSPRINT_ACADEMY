# Quality Assurance Testing Plan
## SkillSprint Academy - Comprehensive Testing Lifecycle

---

## Document Information
- **Version:** 1.0
- **Date:** September 2026
- **Scope:** Full application testing for SkillSprint Academy Purple Team Platform
- **Test Environment:** Local development server (127.0.0.1:52837)

---

## 1. Unit Testing

### Objective
Verify that individual components, functions, and classes operate correctly in isolation.

### Scope
- Flask route handlers
- Service layer functions
- Database models and queries
- Utility functions
- JavaScript pure functions

### Test Cases

#### 1.1 Model Unit Tests
```
TEST-001: User Model
  - Verify user creation with valid data
  - Verify password hashing works correctly
  - Verify authentication method validates password
  - Verify admin flag defaults to False
  - Verify XP calculation updates correctly

TEST-002: Topic Model
  - Verify topic creation with all fields
  - Verify prerequisite relationships
  - Verify difficulty levels 1-5
  - Verify skill_area foreign key relationship
  - Verify active/inactive toggle

TEST-003: TopicLearningModule Model
  - Verify 1:1 relationship with Topic
  - Verify all 5 component fields (theory_md, video_url, lab_guide_md, assessment_md, real_world_md)
  - Verify markdown rendering functions
  - Verify null/empty field handling

TEST-004: Roadmap Model
  - Verify roadmap creation for user
  - Verify roadmap_item relationship
  - Verify status transitions (active, completed, archived)
  - Verify version tracking

TEST-005: AssessmentQuestion Model
  - Verify MCQ options storage as JSON
  - Verify correct_answer index validation
  - Verify difficulty levels
  - Verify active/inactive filtering
```

#### 1.2 Service Layer Unit Tests
```
TEST-010: XP Service
  - Verify XP calculation for different activities
  - Verify streak increment logic
  - Verify streak reset on missed days
  - Verify level calculation from XP thresholds
  - Verify XP cap enforcement per day

TEST-011: Roadmap Engine
  - Verify prerequisite DAG validation
  - Verify topic ordering algorithm
  - Verify time slot allocation
  - Verify schedule generation for given duration
  - Verify curriculum week assignment

TEST-012: AI Tutor Service
  - Verify Ollama API integration
  - Verify rules-based fallback responses
  - Verify context injection (streak, XP, topic)
  - Verify message length validation
  - Verify rate limiting (30 messages/minute)
```

#### 1.3 Route Handler Unit Tests
```
TEST-020: Health Endpoints
  - Verify /health returns 200 with database connection
  - Verify /health/vm returns VM connectivity status
  - Verify offline mode detection

TEST-021: Authentication Routes
  - Verify login with valid credentials
  - Verify login failure handling
  - Verify session management
  - Verify CSRF token generation and validation

TEST-022: Assessment Routes
  - Verify quiz rendering with questions
  - Verify answer submission and scoring
  - Verify explanation display after submission
  - Verify XP award calculation

TEST-023: Dashboard Routes
  - Verify today's tasks calculation
  - Verify streak display
  - Verify XP and level display
  - Verify progress percentage

TEST-024: Roadmap Routes
  - Verify roadmap generation
  - Verify item completion marking
  - Verify schedule modification
  - Verify replan functionality
```

#### 1.4 JavaScript Unit Tests
```
TEST-030: main.js Functions
  - Verify applyUpdate fetches correct URL
  - Verify dismissUpdateBanner hides banner
  - Verify CSRF token extraction from meta tag

TEST-031: update_checker.js Functions
  - Verify getCsrfToken works correctly
  - Verify cookie manipulation functions
  - Verify update check interval logic
  - Verify banner display/hide functions

TEST-032: Exercise Runner Functions
  - Verify Python execution in Pyodide
  - Verify JavaScript sandbox isolation
  - Verify regex validation functions
  - Verify escapeHtml sanitization
```

### Success Criteria
- All tests pass with 0 failures
- Code coverage > 80% for core services
- No deprecated API usage
- All edge cases covered

---

## 2. Integration Testing

### Objective
Verify that modules interact correctly with each other and data flows properly between components.

### Scope
- Blueprint-to-blueprint communication
- Database CRUD operations
- API endpoint integrations
- Frontend-backend communication
- Template rendering with data

### Test Cases

#### 2.1 Blueprint Integration
```
TEST-040: Roadmap-Job Roles Integration
  - Start job role creates roadmap with correct topics
  - Roadmap items link to correct content items
  - Job role detail shows roadmap progress
  - Replan respects job role topic order

TEST-041: Dashboard-Roadmap Integration
  - Dashboard shows correct today's tasks from roadmap
  - Item completion updates dashboard counters
  - XP awarded reflected in dashboard immediately
  - Streak updates on dashboard after activity

TEST-042: Assessment-Roadmap Integration
  - Quiz completion marks roadmap item done
  - Quiz XP award updates roadmap progress
  - Failed quiz allows retry without marking done
  - Topic mastery affects roadmap recommendations

TEST-043: Labs-Roadmap Integration
  - Lab completion awards XP to user
  - Lab completion updates roadmap percentage
  - Lab submission stores proof artifacts
  - Lab verification updates roadmap item status
```

#### 2.2 Database Integration
```
TEST-050: Content Seeding
  - All topics get TopicLearningModule on seed
  - All topics get Labs on seed
  - All topics get AssessmentQuestions on seed
  - Prerequisites create valid DAG
  - No orphaned records after seeding

TEST-051: User Journey Data Flow
  - New user gets default XP (0) and streak (0)
  - Completing activity creates XP log
  - Streak record updates on daily activity
  - Roadmap generates with seeded content

TEST-052: Cascade Delete
  - Deleting roadmap cascades to roadmap_items
  - Deleting topic should preserve or handle learning module
  - Orphaned content items handled gracefully
```

#### 2.3 API Integration
```
TEST-060: Assistant Chat API
  - POST message returns AI response
  - Chat history persists correctly
  - Context topic links chat to topic
  - Rate limiting enforced (30/min)

TEST-061: Update API
  - Update check returns version info
  - Apply update sends correct payload
  - Offline mode blocks update functionality
  - HMAC signature validation (when enabled)
```

#### 2.4 Template Integration
```
TEST-070: Topic Detail Page
  - All 5 tabs render with content
  - Video embeds load correctly
  - Lab links point to correct lab detail
  - Quiz button links to assessment

TEST-071: Dashboard Page
  - Stats display with real data
  - Today's tasks list populates
  - Progress chart renders
  - Mentor suggestions show relevant content
```

### Success Criteria
- All integration flows complete without errors
- Data consistency maintained across operations
- No data loss during complex transactions
- Performance acceptable (< 500ms for API calls)

---

## 3. System Testing

### Objective
Verify end-to-end workflows and complete user scenarios work correctly.

### Scope
- Complete user journeys (onboarding to mastery)
- All navigation paths
- Error handling for edge cases
- Performance under load
- Backup and recovery

### Test Cases

#### 3.1 Complete User Journeys
```
TEST-080: New User Onboarding
  - User visits homepage
  - User creates first roadmap via job role
  - User completes first theory lesson
  - User completes first lab exercise
  - User passes first checkpoint quiz
  - User earns first XP and streak
  - User sees progress in dashboard

TEST-081: Learning Path Completion
  - User follows roadmap for single topic
  - User completes: Theory → Video → Lab → Assessment → Real World
  - User earns all component XP rewards
  - Topic marked complete in roadmap
  - Next topic unlocked

TEST-082: Purple Team Exercise Flow
  - User plans purple team exercise
  - User executes attack phase
  - User logs exercise with notes
  - User analyzes detection results
  - User writes detection rule
  - User completes exercise log

TEST-083: Assessment Flow
  - User takes checkpoint quiz
  - System grades responses
  - System displays explanations
  - System awards XP based on score
  - System updates roadmap status
  - System updates streak
```

#### 3.2 Navigation Testing
```
TEST-090: Main Navigation
  - Homepage loads correctly
  - Roadmap accessible from nav
  - Dashboard accessible from nav
  - Labs accessible from nav
  - Job Roles accessible from nav
  - Assistant accessible from nav

TEST-091: Roadmap Navigation
  - Roadmap view shows all items
  - Calendar view shows schedule
  - Availability editor saves preferences
  - Item completion marks done
  - Schedule changes persist

TEST-092: Topic Navigation
  - Topic detail page loads
  - All 5 tabs accessible
  - Lab links work
  - Quiz links work
  - Breadcrumb navigation works
```

#### 3.3 Error Handling
```
TEST-100: 404 Handling
  - Invalid topic ID shows 404
  - Invalid lab ID shows 404
  - Invalid roadmap item shows 404
  - Friendly error message displayed

TEST-101: 500 Handling
  - Database error shows 500 page
  - Service error shows 500 page
  - User-friendly error displayed
  - No sensitive info leaked

TEST-102: Form Validation
  - Empty required fields rejected
  - Invalid data formats rejected
  - CSRF token validated
  - Rate limiting messages displayed
```

#### 3.4 Performance Testing
```
TEST-110: Response Times
  - Homepage loads < 2 seconds
  - API endpoints respond < 500ms
  - Database queries < 200ms
  - Template rendering < 100ms

TEST-111: Concurrent Users
  - Support 10 simultaneous users
  - No session conflicts
  - Database connections pooled correctly
  - No memory leaks under load
```

### Success Criteria
- All user journeys complete successfully
- Navigation works as expected
- Errors handled gracefully
- Performance meets requirements

---

## 4. Acceptance Testing

### Objective
Validate that the application meets user requirements and is ready for deployment.

### Scope
- User requirement verification
- Use case validation
- Beta user feedback
- Release readiness checklist

### Test Cases

#### 4.1 Functional Requirements
```
TEST-120: Core Features
  - [ ] User can browse and select job roles
  - [ ] User can generate personalized roadmap
  - [ ] User can view roadmap in list and calendar views
  - [ ] User can complete learning activities
  - [ ] User can earn XP and maintain streak
  - [ ] User can take checkpoint quizzes
  - [ ] User can access lab exercises
  - [ ] User can log purple team exercises
  - [ ] User can use AI tutor for help
  - [ ] User can track progress

TEST-121: Content Requirements
  - [ ] All 68 topics have learning modules
  - [ ] All topics have at least 1 lab
  - [ ] All topics have checkpoint quizzes
  - [ ] All prerequisites properly linked
  - [ ] Video content available for key topics
```

#### 4.2 Use Case Validation
```
TEST-130: Student Use Case
  "As a student, I want to learn cybersecurity from scratch"
  - [ ] Beginner can understand roadmap structure
  - [ ] Foundational topics available first
  - [ ] Learning path is clear and sequential
  - [ ] Progress is visible and motivating

TEST-131: Professional Use Case
  "As a security professional, I want to fill skill gaps"
  - [ ] Topics organized by skill area
  - [ ] Difficulty ratings accurate
  - [ ] Advanced topics accessible
  - [ ] Purple team exercises available

TEST-132: Career Changer Use Case
  "As a career changer, I want structured learning"
  - [ ] No prior knowledge assumed
  - [ ] Prerequisites clearly shown
  - [ ] Time estimates accurate
  - [ ] Certification paths identified
```

#### 4.3 User Interface Acceptance
```
TEST-140: Visual Checkpoints
  - [ ] Dark theme displays correctly
  - [ ] All text readable
  - [ ] Buttons have hover states
  - [ ] Forms have validation feedback
  - [ ] Loading states displayed
  - [ ] Error messages styled appropriately

TEST-141: Responsive Design
  - [ ] Desktop view complete
  - [ ] Tablet view usable
  - [ ] Mobile view functional (if required)
```

#### 4.4 Release Checklist
```
TEST-150: Pre-Release Verification
  - [ ] All 16 unit tests pass
  - [ ] No console errors in browser
  - [ ] All templates render correctly
  - [ ] Database migrations applied
  - [ ] Seed data loaded
  - [ ] Static files served correctly
  - [ ] No hardcoded secrets
  - [ ] CSP headers configured
  - [ ] CSRF protection enabled
  - [ ] Rate limiting configured
```

### Success Criteria
- All requirements verified as implemented
- User feedback collected and incorporated
- No critical bugs remaining
- Stakeholder sign-off received

---

## 5. Security Testing

### Objective
Identify and remediate security vulnerabilities before release.

### Scope
- Authentication and authorization
- Input validation and sanitization
- Session management
- CSRF/XSS/SQLi protection
- Access control enforcement
- Data protection

### Test Cases

#### 5.1 Authentication & Authorization
```
TEST-160: Authentication
  - [ ] Default credentials not exploitable
  - [ ] Passwords properly hashed (bcrypt)
  - [ ] Session tokens cryptographically secure
  - [ ] Login rate limiting enforced
  - [ ] Failed login attempts logged

TEST-161: Authorization
  - [ ] Users cannot access other users' data
  - [ ] Admin routes require admin privileges
  - [ ] API endpoints validate ownership
  - [ ] File access controls enforced
```

#### 5.2 Input Validation
```
TEST-170: XSS Prevention
  - [ ] User input escaped in templates
  - [ ] AI chat responses sanitized
  - [ ] Markdown rendering safe
  - [ ] No inline script execution
  - [ ] CSP headers block inline scripts

TEST-171: SQL Injection Prevention
  - [ ] All queries use parameterized statements
  - [ ] ORM properly escapes input
  - [ ] No SQL in user-controlled strings
  - [ ] Error messages don't expose queries

TEST-172: Command Injection Prevention
  - [ ] No shell commands from user input
  - [ ] File paths validated before access
  - [ ] No path traversal possible
```

#### 5.3 Session Management
```
TEST-180: Session Security
  - [ ] Session cookies HttpOnly
  - [ ] Session cookies Secure (when HTTPS)
  - [ ] Session timeout enforced
  - [ ] Session regeneration on login
  - [ ] Concurrent session limits (if applicable)
```

#### 5.4 CSRF Protection
```
TEST-190: CSRF Validation
  - [ ] All POST/PUT/DELETE require CSRF token
  - [ ] CSRF tokens validated server-side
  - [ ] Tokens expire after use
  - [ ] AJAX requests include CSRF header
```

#### 5.5 Security Headers
```
TEST-200: HTTP Security Headers
  - [ ] Content-Security-Policy configured
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] Strict-Transport-Security (if HTTPS)
```

### Success Criteria
- No critical or high vulnerabilities
- All medium vulnerabilities documented
- Security review completed
- Penetration test passed

---

## 6. Comprehensive Quality Assurance

### Objective
Final holistic review ensuring all components work together seamlessly and content is accurate.

### Scope
- End-to-end workflow validation
- Content accuracy review
- UX consistency check
- Documentation verification
- Performance baseline verification

### Test Cases

#### 6.1 End-to-End Workflows
```
TEST-210: Complete Learning Flow
  1. User starts at homepage
  2. User selects "SOC Analyst" job role
  3. Roadmap generates with 40+ topics
  4. User completes first week of activities
  5. User earns first level (Level 2)
  6. User completes first domain
  7. User takes domain assessment
  8. User reviews progress analytics
  9. All XP and streak calculated correctly
  10. User continues through full curriculum

TEST-211: Purple Team Exercise Flow
  1. User plans exercise for "Kerberoasting"
  2. User reads lab guide
  3. User sets up lab environment
  4. User executes attack in Kali VM
  5. User observes detection in Wazuh
  6. User writes detection rule
  7. User logs exercise findings
  8. User earns Purple Team XP
  9. Coverage metrics update
```

#### 6.2 Content Accuracy Review
```
TEST-220: Curriculum Content
  - [ ] All 68 topics have meaningful content
  - [ ] Prerequisites are logically correct
  - [ ] Difficulty ratings match content complexity
  - [ ] Learning objectives are achievable
  - [ ] Lab instructions are executable
  - [ ] Quiz questions have correct answers
  - [ ] Explanations are accurate

TEST-221: Technical Accuracy
  - [ ] MITRE ATT&CK mappings correct
  - [ ] Command syntax accurate
  - [ ] Tool names and versions current
  - [ ] Links point to valid resources
```

#### 6.3 UX Consistency
```
TEST-230: Design Consistency
  - [ ] All buttons have consistent styling
  - [ ] Color scheme uniform across pages
  - [ ] Typography consistent
  - [ ] Spacing and layout aligned
  - [ ] Dark theme fully applied

TEST-231: Interaction Consistency
  - [ ] All forms submit with Enter key
  - [ ] All buttons have loading states
  - [ ] All async operations show feedback
  - [ ] Error states consistent
```

#### 6.4 Documentation Review
```
TEST-240: User Documentation
  - [ ] Getting started guide accurate
  - [ ] FAQ addresses common questions
  - [ ] Error messages actionable
  - [ ] Help tooltips present

TEST-241: Developer Documentation
  - [ ] API endpoints documented
  - [ ] Database schema documented
  - [ ] Deployment guide accurate
  - [ ] Configuration options documented
```

#### 6.5 Final Verification
```
TEST-250: Pre-Deployment Checklist
  - [ ] All tests passing (16/16)
  - [ ] No console errors
  - [ ] No 404 resources
  - [ ] Database seeded and verified
  - [ ] Static files fingerprinted
  - [ ] Logs not exposing sensitive data
  - [ ] Backup strategy documented
  - [ ] Rollback plan documented
```

### Success Criteria
- All workflows complete without manual intervention
- Content accurate and current
- UX consistent and polished
- Documentation complete and accurate
- Ready for production deployment

---

## Test Execution Schedule

| Phase | Duration | Timing |
|-------|----------|--------|
| Unit Testing | Continuous | During development |
| Integration Testing | 1 week | After feature completion |
| System Testing | 1 week | Before release |
| Acceptance Testing | 1 week | UAT with stakeholders |
| Security Testing | 1 week | Before release |
| Comprehensive QA | 3 days | Final review |

---

## Bug Severity Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Data loss, security breach, complete failure | 24 hours |
| High | Major feature broken, workarounds difficult | 1 week |
| Medium | Feature partially works, workaround exists | 2 weeks |
| Low | Cosmetic issues, minor inconvenience | Next release |

---

## Test Deliverables

1. **Test Plan** (this document)
2. **Test Cases** (test code in test_comprehensive.py)
3. **Test Reports** (pytest output logs)
4. **Bug Reports** (GitHub Issues)
5. **Security Assessment Report** (separate document)
6. **Release Sign-off** (stakeholder approval)

---

*Quality Assurance Plan Version 1.0 | SkillSprint Academy*
