# MongoDB Atlas IP Whitelist

**Purpose:** Track authorized IP addresses for MongoDB Atlas access  
**Last Reviewed:** February 25, 2026  
**Review Frequency:** Monthly (every 1st of the month)  
**Owner:** Security Team

---

## 📋 Current IP Whitelist

### Production Environment

| IP Address | CIDR | Description | Added Date | Expires | Owner | Status |
|------------|------|-------------|------------|---------|-------|--------|
| *None configured* | - | Production server | - | - | - | ⚠️ **TODO** |

**Notes:**
- Production IPs should never expire
- Verify IP is static before adding
- Use VPC peering instead of public IP whitelist (recommended)

---

### Staging Environment

| IP Address | CIDR | Description | Added Date | Expires | Owner | Status |
|------------|------|-------------|------------|---------|-------|--------|
| *None configured* | - | Staging server | - | - | - | ⚠️ **TODO** |

**Notes:**
- Staging can use same security as production
- Consider separate MongoDB cluster for staging

---

### Development Environment

| IP Address | CIDR | Description | Added Date | Expires | Owner | Status |
|------------|------|-------------|------------|---------|-------|--------|
| `0.0.0.0/0` | /0 | **LOCAL DEV ONLY** | Feb 25, 2026 | Never | Dev Team | ⚠️ **INSECURE** |

**⚠️ WARNING:** 
- `0.0.0.0/0` allows access from **ANYWHERE IN THE WORLD**
- **MUST BE REMOVED before production deployment**
- If using MongoDB Atlas for development, replace with specific developer IPs

**For local development:**
- Use local MongoDB instead of Atlas (`mongodb://localhost:27017/`)
- Or whitelist specific developer IPs (see below)

---

### Temporary Developer Access

| IP Address | CIDR | Description | Added Date | Expires | Owner | Status |
|------------|------|-------------|------------|---------|-------|--------|
| *Example:* 198.51.100.45 | /32 | John Doe - Home IP | Feb 25, 2026 | Mar 4, 2026 | John Doe | ✅ Active |

**Rules for Temporary Access:**
- Maximum duration: 7 days
- Must specify expiration date
- Review and remove expired IPs weekly
- Developer must use VPN when possible

---

### CI/CD Infrastructure

| IP Address | CIDR | Description | Added Date | Expires | Owner | Status |
|------------|------|-------------|------------|---------|-------|--------|
| *None configured* | - | GitHub Actions runner | - | Never | DevOps | ⚠️ **TODO** |

**Notes:**
- GitHub Actions uses dynamic IPs (consider self-hosted runner)
- For self-hosted runners, whitelist runner server IP
- For cloud CI/CD, use VPC peering

---

### VPN/Office Network

| IP Address | CIDR | Description | Added Date | Expires | Owner | Status |
|------------|------|-------------|------------|---------|-------|--------|
| *Example:* 203.0.113.0 | /24 | Corporate VPN subnet | Feb 25, 2026 | Never | IT Dept | ✅ Active |

**Notes:**
- Use /24 subnet for entire VPN range
- Verify VPN IP range with IT department
- Preferred over individual developer IPs

---

## 🔒 Security Best Practices

### ✅ Allowed

- **Static IPs**: From production servers, VPNs, permanent infrastructure
- **VPC Peering**: AWS, Azure, GCP (preferred over IP whitelist)
- **Private Endpoints**: Azure Private Link, AWS PrivateLink
- **Temporary IPs**: With clear expiration dates (max 7 days)
- **CIDR /32**: For single IP addresses
- **CIDR /24**: For VPN subnets (documented and approved)

### ❌ Prohibited

- **0.0.0.0/0**: In production (anywhere access)
- **Dynamic IPs**: Home internet without static IP
- **Public Wi-Fi**: Coffee shops, airports, hotels
- **Shared IPs**: Multiple developers on same IP without VPN
- **Undocumented IPs**: Every IP must have owner and purpose
- **Expired entries**: Remove immediately after expiration

---

## 📝 IP Whitelist Management

### Adding a New IP

**For Production/Staging:**

1. **Request:**
   ```
   Environment: [Production/Staging]
   IP Address: [x.x.x.x]
   CIDR: [/32 for single IP]
   Purpose: [e.g., "AWS EC2 production server"]
   Owner: [Your Name]
   Static/Dynamic: [Static required for prod]
   ```

2. **Approval Process:**
   - Submit request to security team
   - Security team verifies request
   - Add to MongoDB Atlas Network Access
   - Update this document
   - Notify team via Slack

3. **Add to MongoDB Atlas:**
   - Login to [MongoDB Atlas](https://cloud.mongodb.com/)
   - Navigate to **Security** → **Network Access**
   - Click **Add IP Address**
   - Enter IP/CIDR and description
   - Save changes
   - Wait 2-5 minutes for propagation

**For Temporary Developer Access:**

1. **Self-Service:**
   - Check if your IP is already whitelisted
   - Add your IP with 7-day expiration
   - Update "Temporary Developer Access" table in this document
   - Notify team in #backend channel

2. **Get Your IP:**
   ```powershell
   # Windows
   Invoke-RestMethod -Uri https://api.ipify.org

   # Or visit: https://whatismyipaddress.com/
   ```

3. **Add to Atlas:**
   - IP Address: [Your IP]/32
   - Description: "[Your Name] - [Location] - Expires [Date]"
   - Set calendar reminder to remove

### Removing an IP

**When to Remove:**
- IP has expired (check weekly)
- Server decommissioned
- Developer left company
- Environment no longer in use
- Security incident involving that IP

**Removal Process:**

1. **Verify safe to remove:**
   - Check if any active connections
   - Notify affected parties 24h in advance (non-emergency)
   - For emergency (security incident), remove immediately

2. **Remove from MongoDB Atlas:**
   - Login to MongoDB Atlas
   - Security → Network Access
   - Find IP in list
   - Click **Delete**
   - Confirm deletion

3. **Update Documentation:**
   - ~~Strike through~~ entry in this document
   - Add "Removed: [Date] - Reason: [...]"
   - Archive in git history

### Emergency Access

**Scenario:** Developer needs immediate access from unknown IP

**Procedure:**

1. **Request via Slack:**
   ```
   @security-team Urgent: Need MongoDB access
   Current IP: [x.x.x.x]
   Reason: [Production incident/Critical fix]
   Duration: [1-24 hours]
   ```

2. **Security Team Response (< 30 min SLA):**
   - Verify identity
   - Add IP with 24h expiration
   - Enable audit logging for that IP
   - Monitor access during emergency window

3. **Post-Emergency:**
   - Remove temporary IP after incident
   - Review access logs
   - Update runbooks if needed

---

## 🔍 Monitoring & Auditing

### Weekly Review (Every Monday)

- [ ] Check for expired temporary IPs
- [ ] Remove stale entries
- [ ] Verify all IPs have owner documentation
- [ ] Review MongoDB Atlas access logs for unusual activity

### Monthly Audit (1st of Month)

- [ ] Review all production IPs still valid
- [ ] Confirm staging IPs still needed
- [ ] Remove any undocumented IPs
- [ ] Update this document header with review date
- [ ] Report findings to security team

### Automated Alerts

Configure MongoDB Atlas alerts for:
- ✅ Connection attempts from non-whitelisted IPs
- ✅ Multiple failed authentication attempts
- ✅ New IP address added to whitelist
- ✅ Database user created/modified

**Alert Thresholds:**
- Failed auth: > 5 attempts in 10 minutes
- Non-whitelisted access: Any attempt
- Configuration changes: All changes

---

## 🚀 Migration to VPC Peering

**Recommended for Production**

### Benefits

- ✅ No public IP exposure
- ✅ Traffic stays on cloud provider network
- ✅ No IP whitelist management
- ✅ Better performance (lower latency)
- ✅ Enhanced security

### Setup (AWS Example)

1. **MongoDB Atlas:**
   - Network Access → Peering → Add Peering Connection
   - Provider: AWS
   - Region: [your AWS region]
   - VPC CIDR: [your VPC CIDR]

2. **AWS:**
   - Accept peering request in VPC console
   - Update route tables
   - Update security groups

3. **Update Application:**
   - Use private connection string
   - No changes to application code
   - Remove public IP whitelist entries

4. **Verify:**
   ```powershell
   # Test connection from EC2 instance
   mongosh "mongodb+srv://cluster-internal.mongodb.net/"
   ```

### Timeline

- Planning: 1 day
- Setup: 2-4 hours
- Testing: 1 day
- Migration: 1 day (maintenance window)

**Total: 3-4 days**

---

## 📞 Contacts

| Role | Contact | Slack | Responsibilities |
|------|---------|-------|------------------|
| Security Lead | [Name] | @security-lead | Approve production IPs |
| DevOps Lead | [Name] | @devops-lead | VPC peering, infrastructure |
| On-Call Engineer | [Name] | @oncall | Emergency access requests |

---

## 📚 References

- [MongoDB Atlas Network Security Documentation](https://docs.atlas.mongodb.com/security-vpc-peering/)
- [AWS VPC Peering Guide](https://docs.aws.amazon.com/vpc/latest/peering/)
- [Azure Private Link](https://docs.microsoft.com/en-us/azure/private-link/)
- [GCP Private Service Connect](https://cloud.google.com/vpc/docs/private-service-connect)
- [Verif-AI Security Best Practices](SECURITY_BEST_PRACTICES.md)
- [Verif-AI Deployment Guide](DEPLOYMENT.md)

---

## 🔄 Change Log

| Date | Change | Author | Reason |
|------|--------|--------|--------|
| Feb 25, 2026 | Initial document created | Security Team | Gap #3 implementation |
| [Future] | [Change description] | [Your Name] | [Reason] |

---

## 📝 Template for New Entries

**Copy this template when adding new IPs:**

```markdown
| [IP_ADDRESS] | /32 | [Server description] | [MMM DD, YYYY] | [Never/Date] | [Owner Name] | ✅ Active |
```

**Example:**
```markdown
| 52.12.34.56 | /32 | Production API server (AWS us-west-2) | Jan 15, 2026 | Never | DevOps Team | ✅ Active |
```

---

**Last Updated:** February 25, 2026  
**Next Review:** March 1, 2026  
**Document Version:** 1.0
