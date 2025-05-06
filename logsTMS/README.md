# Test model with perturbation results
Note that allTests.zip contains results for the perturbation analysis. Each log-subdirectory within the folder is created by running the model creation with the flag `s`.
`python postProcessing.py -lv -d logsTMS/log_Llama3.1-8B-HF`
`python postProcessing.py -lv -d logsTMS/log_Llama3.1-8B-Q4`
`python testModelCreationJoh.py -n Phi4-Q4 -s`

Based on the results wihtin that folder, Levensthein `lv` or numerical `nm` evaluations can be performed and visualized.
`python postProcessing.py -lv -d logsTMS/log_Llama3.1-8B-HF`
`python postProcessing.py -lv -d logsTMS/log_Llama3.1-8B-Q4`
`python postProcessing.py -nm -d logsTMS/log_Phi4-Q4`
