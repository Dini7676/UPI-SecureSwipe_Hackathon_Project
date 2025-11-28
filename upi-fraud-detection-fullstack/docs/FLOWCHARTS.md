# Flowcharts (ASCII)

## OTP Login
```
[Enter Mobile/Email]
      |
  [Send OTP] --> [Redis setex]
      |
  [Receive OTP]
      |
  [Verify OTP] --> [Redis get]
      |                 |
   [Valid?] ---No--> [Error]
      |
     Yes
      |
 [Create/Fetch User] --> [Issue JWT]
```

## Fraud Scoring
```
[Request Score] --> [Build features]
      |
 [Rule-based engine] --> [risk_score]
      |
 [Store Transaction] --> [FraudLog]
```
