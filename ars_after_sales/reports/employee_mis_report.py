from odoo import models, fields,api,tools


class CustomerEnqDumpsMis(models.Model):
    _name          = "employee_mis_report"
    _description   = "Customer Enquiry Dumps MIS Report"
    _auto          = False

    dealer_name = fields.Char(string="Dealer Name")
    dealer_code = fields.Char(string="Dealer Code")
    # location = fields.Char(string="Location")
    emp_code = fields.Char(string="Employee Code")
    employee = fields.Char(string="Employee Name")
    job_title = fields.Char(string="Job title")
    department = fields.Char(string="Department")
    birthday = fields.Char(string="Date of Birth")
    gender = fields.Char(string="Gender")
    marital = fields.Char(string="Marital Status")
    blood_group = fields.Char(string="Blood Group")
    education_details = fields.Char(string="Education Details")
    date_of_joining = fields.Date(string="Joining Date")
    date_of_exit = fields.Date(string="Exit Date")
    employement_type = fields.Selection([('probationer', 'Probationer'),('permanent', 'Permanent'),('contract', 'Contract')])
    status = fields.Char(string="Status")
    aadhar_id = fields.Char(string="Aadhar No")
    passport = fields.Char(string="Passport")
    voter_id = fields.Char(string="Voter ID")
    pan_no = fields.Char(String="PAN No")
    account_holder = fields.Char(string="Name (as per Bank A/C)")
    bank_name = fields.Char(string="Bank Name")
    ifsc = fields.Char(string="IFSC")
    acc_number = fields.Char(string="Accout Number")
 


    @api.model_cr_context
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f""" CREATE or REPLACE VIEW %s as ( 
            select row_number() over() AS id,
            b.name as dealer_name,b.dealer_code as dealer_code,a.name as employee,c.name as job_title,
            d.name as department,a.birthday as birthday,a.gender as gender,a.marital as marital,
            case
            when a.active = 'True' then 'Active'
            else 'Not Active' 
            end as status,
            a.passport_id passport,e.acc_number as acc_number,
            f.name as bank_name,f.bic as ifsc,g.name as account_holder,g.pan_no as pan_no,
            a.emp_code as emp_code,a.blood_group as blood_group,a.education_details as education_details,
            a.aadhar_id as aadhar_id,a.voter_id as voter_id,a.employement_type as employement_type,
            a.date_of_joining as date_of_joining,a.date_of_exit as date_of_exit 
            from hr_employee a join res_company b on a.company_id = b.id 
            join hr_job c on a.job_id=c.id
            join hr_department d on a.department_id=d.id
            join res_partner_bank e on a.bank_account_id=e.id
            join res_bank f on e.bank_id=f.id
            join res_partner g on e.partner_id=g.id )""" % (self._table))
