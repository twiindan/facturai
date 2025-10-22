1. Descripción General y proposito del proyecto

Objetivo Principal: Este es un programa para una aplicación de parseo y logica de facturas. 

Dominio del negocio: Facturas asesoria

2. Tecnologia:

- Lenguaje: Python 3.12
- Pruebas: Pytest
- Usa Pydantic para definir los modelos necesarios

3. Guia de Estilos 
- PEP8
- Nomenclatura:
    - variables y funciones snake_case
    - clases PascalCase
    - Utulizar type hints de Python en todas las firmas de funciones y metodos


4. Estructura y arquitectura:
- Utiliza buenas practicas de desarrollo
- Minimiza las dependencias
- Usa logging para detallar que esta pasando
- Todo el codigo fuente estara en la carpeta src. Existira una carpeta de Data donde poder dejar las facturas a procesar

## Documentacion

- Todo tiene que estar documentado para que cualquier persona pueda entenderlo 

Instructions for Gemini
If you think I've provided valuable context for future developments, ask me to include this context in GEMINI.md.

Version Control
- Non-trivial edits must be tracked in git
- Create WIP branches for new work
- Commit frequently throughout development
- Never throw away implementations without explicit permission

Testing Requirements
- NO EXCEPTIONS POLICY: All projects MUST have:
	- Unit tests
- The only way to skip tests: Fran EXPLICITLY states "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME."

	- Tests must comprehensively cover all functionality
	- Test output must be pristine to pass
	- Never ignore system/test output - logs contain critical information

Code Writing

- We STRONGLY prefer simple, clean, maintainable solutions over clever or complex ones. Readability and maintainability are PRIMARY CONCERNS, even at the cost of conciseness or performance.
- YOU MUST make the SMALLEST reasonable changes to achieve the desired outcome.
- YOU MUST MATCH the style and formatting of surrounding code, even if it differs from standard style guides. Consistency within a file trumps external standards.
- YOU MUST NEVER make code changes unrelated to your current task. If you notice something that should be fixed but is unrelated, document it rather than fixing it immediately.
- YOU MUST NEVER remove code comments unless you can PROVE they are actively false. Comments are important documentation and must be preserved.
- All code files MUST start with a brief 2-line comment explaining what the file does. Each line MUST start with "ABOUTME: " to make them easily greppable.
- YOU MUST NEVER refer to temporal context in comments (like "recently refactored"). Comments should be evergreen and describe the code as it is.
- YOU MUST NEVER throw away implementations to rewrite them without EXPLICIT permission. If you're considering this, YOU MUST STOP and ask first.
- YOU MUST NEVER use temporal naming conventions like 'improved', 'new', or 'enhanced'. All naming should be evergreen.
- YOU MUST NOT change whitespace unrelated to code you're modifying.


## Version Control

- For non-trivial edits, all changes MUST be tracked in git.
- If the project isn't in a git repo, YOU MUST STOP and ask permission to initialize one.
- If there are uncommitted changes or untracked files when starting work, YOU MUST STOP and ask how to handle them. Suggest committing existing work first.
- When starting work without a clear branch for the current task, YOU MUST create a WIP branch.
- YOU MUST commit frequently throughout the development process.

## Getting Help

- Always ask for clarification rather than making assumptions
- Stop and ask for help when stuck, especially when human input would be valuable
- If considering an exception to any rule, stop and get explicit permission from Fran first

## Testing

- Tests MUST comprehensively cover ALL implemented functionality. 
- YOU MUST NEVER ignore system or test output - logs and messages often contain CRITICAL information.
- Test output MUST BE PRISTINE TO PASS.
- If logs are expected to contain errors, these MUST be captured and tested.
- NO EXCEPTIONS POLICY: ALL projects MUST have unit tests, integration tests, AND end-to-end tests. The only way to skip any test type is if Fran EXPLICITLY states: "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME."


## Compliance Check
Before submitting any work, verify that you have followed ALL guidelines above. If you find yourself considering an exception to ANY rule, YOU MUST STOP and get explicit permission from Fran first.
