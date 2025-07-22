# API Spec Folder

This folder contains the OpenAPI and HTTP specification files for the document extraction service, following the structure and style of the `sample` folder.

## Structure
- Place all OpenAPI (YAML) files and HTTP sample request files here.
- Each API or endpoint should have a clear, descriptive filename and accompanying documentation if needed.

## References
- See the `sample` folder for examples of API documentation and request formats.

## Example Files
- `document-extraction-api.yaml` — OpenAPI 3.0/3.1 spec for your main extraction API
- `document-extraction-api.http` — Sample HTTP requests for testing endpoints

---

To add a new API spec:
1. Copy the structure from `sample/delivery-order-process-api.yaml` and modify for your endpoints.
2. Add HTTP request samples as in `sample/sample-api.http`.
3. Document any authentication, parameters, and expected responses.
