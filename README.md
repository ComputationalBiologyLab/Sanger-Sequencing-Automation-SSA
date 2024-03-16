# Sanger-Sequencing-Automation-SSA


To use on SSA
1. Choose the .zip file corresponding to your operating system.
2. Extract the contents of the .zip file.
3. Simply double-click the .exe file to run the program

### To run the code

1. Clone the project: git clone https://github.com/ComputationalBiologyLab/Sanger-Sequencing-Automation-SSA.git or simply download the code from this repository
2. Create virtual environment: python -m venv venv
3. Activate the environment: Mac&Linux: source venv/bin/activate on Windows: venv/Scripts/activate
4. Install dependencies: pip install -r requirements.txt
5. Run the code: python desktop-app-pyqt/app.py


Instructions to use the application:

1. Upon launching SSA, navigate to the Quick Guide page and review the instructions provided.

2. Before proceeding, ensure that the appropriate configurations are set up.

**Important Note**: As per NCBI API regulations, we're limited to a maximum of 100 requests per day. Exceeding this limit may result in reduced speed or being banned from access.

If you require more requests:

- Choose "Send more than 100 blast requests per day." This option allows the application to pause once reaching the 100-request limit and resume the next day.
- Select either Blastnr, Blastnt, or both, depending on your needs (this choice influences the number of requests made).
- Specify whether you're working with single files or paired files, as this also affects the number of requests sent.
- To overwrite previously generated blast files, select "Overwrite already generated files."
- A summary of the request count will be displayed in the black box for your reference."

![image](https://github.com/ComputationalBiologyLab/Sanger-Sequencing-Automation-SSA/assets/97539613/26df9e1c-0abf-49a3-8ebe-46f9a24c4f6a)

3.  Results page will show results for each sample

![image](https://github.com/ComputationalBiologyLab/Sanger-Sequencing-Automation-SSA/assets/97539613/247d02c4-a8bf-4414-a9e1-dcb61eddb40e)



4. In addition to the Summary page for  all


![image](https://github.com/ComputationalBiologyLab/Sanger-Sequencing-Automation-SSA/assets/97539613/8ab2f443-59c1-4c7e-ab54-1685cd834c95)


