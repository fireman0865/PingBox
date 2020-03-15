# Webhooks

A webhook is a mechanism for conveying to some external system a change that took place in NetBox. For example, you may want to notify a monitoring system whenever a device status is changed in NetBox. This can be done by creating a webhook for the device model in NetBox. When NetBox detects a change to a device, an HTTP request containing the details of the change and who made it be sent to the specified receiver. Webhooks are configured in the admin UI under Extras > Webhooks.

## Configuration

* **Name** - A unique name for the webhook. The name is not included with outbound messages.
* **Object type(s)** - The type or types of NetBox object that will trigger the webhook.
* **Enabled** - If unchecked, the webhook will be inactive.
* **Events** - A webhook may trigger on any combination of create, update, and delete events. At least one event type must be selected.
* **HTTP method** - The type of HTTP request to send. Options include GET, POST, PUT, PATCH, and DELETE.
* **URL** - The fuly-qualified URL of the request to be sent. This may specify a destination port number if needed.
* **HTTP content type** - The value of the request's `Content-Type` header. (Defaults to `application/json`)
* **Additional headers** - Any additional headers to include with the request (optional). Add one header per line in the format `Name: Value`. Jinja2 templating is supported for this field (see below).
* **Body template** - The content of the request being sent (optional). Jinja2 templating is supported for this field (see below). If blank, NetBox will populate the request body with a raw dump of the webhook context. (If the HTTP cotent type is set to `application/json`, this will be formatted as a JSON object.)
* **Secret** - A secret string used to prove authenticity of the request (optional). This will append a `X-Hook-Signature` header to the request, consisting of a HMAC (SHA-512) hex digest of the request body using the secret as the key.
* **SSL verification** - Uncheck this option to disable validation of the receiver's SSL certificate. (Disable with caution!)
* **CA file path** - The file path to a particular certificate authority (CA) file to use when validating the receiver's SSL certificate (optional).

## Jinja2 Template Support

[Jinja2 templating](https://jinja.palletsprojects.com/) is supported for the `additional_headers` and `body_template` fields. This enables the user to convey change data in the request headers as well as to craft a customized request body. Request content can be crafted to enable the direct interaction with external systems by ensuring the outgoing message is in a format the receiver expects and understands.

For example, you might create a NetBox webhook to [trigger a Slack message](https://api.slack.com/messaging/webhooks) any time an IP address is created. You can accomplish this using the following configuration:

* Object type: IPAM > IP address
* HTTP method: POST
* URL: <Slack incoming webhook URL>
* HTTP content type: `application/json`
* Body template: `{"text": "IP address {{ data['address'] }} was created by {{ username }}!"}`

### Available Context

The following data is available as context for Jinja2 templates:

* `event` - The type of event which triggered the webhook: created, updated, or deleted.
* `model` - The NetBox model which triggered the change.
* `timestamp` - The time at which the event occurred (in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format).
* `username` - The name of the user account associated with the change.
* `request_id` - The unique request ID. This may be used to correlate multiple changes associated with a single request.
* `data` - A serialized representation of the object _after_ the change was made. This is typically equivalent to the model's representation in NetBox's REST API.

### Default Request Body

If no body template is specified, the request body will be populated with a JSON object containing the context data. For example, a newly created site might appear as follows:

```no-highlight
{
    "event": "created",
    "timestamp": "2020-02-25 15:10:26.010582+00:00",
    "model": "site",
    "username": "jstretch",
    "request_id": "fdbca812-3142-4783-b364-2e2bd5c16c6a",
    "data": {
        "id": 19,
        "name": "Site 1",
        "slug": "site-1",
        "status": 
            "value": "active",
            "label": "Active",
            "id": 1
        },
        "region": null,
        ...
    }
}
```

## Webhook Processing

When a change is detected, any resulting webhooks are placed into a Redis queue for processing. This allows the user's request to complete without needing to wait for the outgoing webhook(s) to be processed. The webhooks are then extracted from the queue by the `rqworker` process and HTTP requests are sent to their respective destinations. The current webhook queue and any failed webhooks can be inspected in the admin UI under Django RQ > Queues.

A request is considered successful if the response has a 2XX status code; otherwise, the request is marked as having failed. Failed requests may be retried manually via the admin UI.
