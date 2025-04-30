// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Amplify } from "aws-amplify";
import { fetchAuthSession } from "aws-amplify/auth";
import { post, get, del } from "aws-amplify/api";
import { Campaign } from "@/contexts/campaign-context";
import { getErrorMessage } from "./utils";

const env = import.meta.env;

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: env.VITE_COGNITO_USER_POOL_ID,
      userPoolClientId: env.VITE_COGNITO_USER_POOL_CLIENT_ID,
      identityPoolId: env.VITE_COGNITO_IDENTITY_POOL_ID,
    },
  },
});

const existingConfig = Amplify.getConfig();

Amplify.configure({
  ...existingConfig,
  API: {
    REST: {
      [env.VITE_API_NAME]: {
        endpoint: env.VITE_API_GATEWAY_REST_API_ENDPOINT,
        region: env.VITE_AWS_REGION,
      },
    },
  },
});

const session = await fetchAuthSession();
const authToken = session.tokens?.idToken?.toString();

const defaultRestInput = {
  apiName: env.VITE_API_NAME,
  options: {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  },
};

export async function getCampaigns() {
  try {
    const restOperation = get({
      ...defaultRestInput,
      path: "/campaigns",
    });
    const response = await restOperation.response;
    return response.body.json();
  } catch (e: unknown) {
    console.log("GET call failed: ", getErrorMessage(e));
  }
}

export async function getCampaign(campaignId: string) {
  try {
    const restOperation = get({
      ...defaultRestInput,
      path: `/campaigns/${campaignId}`,
    });
    const response = await restOperation.response;
    return response.body.json();
  } catch (e: unknown) {
    console.log("GET call failed: ", getErrorMessage(e));
  }
}

export async function createCampaign(campaign: Campaign) {
  try {
    const restOperation = post({
      ...defaultRestInput,
      path: `/campaigns`,
      options: {
        ...defaultRestInput.options,
        body: campaign,
      },
    });
    const response = await restOperation.response;
    return response.body.json();
  } catch (e: unknown) {
    console.log("POST call failed: ", getErrorMessage(e));
  }
}

export async function deleteCampaign(campaignId: string) {
  try {
    const restOperation = del({
      ...defaultRestInput,
      path: `/campaigns/${campaignId}`,
    });
    return await restOperation.response;
  } catch (e: unknown) {
    console.log("DELETE call failed: ", getErrorMessage(e));
  }
}

export async function getReferences(campaignId: string) {
  try {
    const restOperation = post({
      ...defaultRestInput,
      path: `/references/${campaignId}`,
    });
    const response = await restOperation.response;
    return response;
  } catch (e: unknown) {
    console.log("POST call failed: ", getErrorMessage(e));
  }
}

export async function getPresignedImageUrl(s3path: string) {
  try {
    const restOperation = post({
      ...defaultRestInput,
      path: `/presign`,
      options: {
        ...defaultRestInput.options,
        body: {
          s3Path: s3path,
        },
      },
    });
    const response = await restOperation.response;
    return response.body.json();
  } catch (e: unknown) {
    console.log("POST call failed: ", getErrorMessage(e));
  }
}

export async function getSuggestion(campaignId: string, references: string[]) {
  try {
    const restOperation = post({
      ...defaultRestInput,
      path: `/suggestion/${campaignId}`,
      options: {
        ...defaultRestInput.options,
        body: { references },
      },
    });
    const response = await restOperation.response;
    return response;
  } catch (e: unknown) {
    console.log("POST call failed: ", getErrorMessage(e));
  }
}

export async function getGeneratedImage(campaignId: string, prompt: string) {
  try {
    const restOperation = post({
      ...defaultRestInput,
      path: `/generate_images/${campaignId}`,
      options: {
        ...defaultRestInput.options,
        body: {
          prompt: prompt,
        },
      },
    });
    const response = await restOperation.response;
    return response;
  } catch (e: unknown) {
    console.log("POST call failed: ", getErrorMessage(e));
  }
}
